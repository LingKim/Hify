"""Agent module business services."""

from __future__ import annotations

from fastapi import status
from sqlalchemy import bindparam, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.errors import AgentErrorCode
from app.agent.model import Agent, AgentKnowledgeBinding, AgentToolBinding
from app.agent.schema import (
    AgentAdminCreateReq,
    AgentAdminUpdateReq,
    AgentConfigPreviewResp,
    AgentDetailResp,
    AgentKnowledgeBindingInput,
    AgentKnowledgeBindingResp,
    AgentListParams,
    AgentModelSummaryResp,
    AgentRuntimePreviewResp,
    AgentSummaryResp,
    AgentToolBindingInput,
    AgentToolBindingResp,
)
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException
from app.core.responses import PageResult
from app.tool.model import Tool


class AgentService:
    """Agent service with aggregated configuration CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the agent service."""
        self.db = db

    async def preview(self) -> AgentConfigPreviewResp:
        """Return the legacy agent module preview payload."""
        return AgentConfigPreviewResp(
            module="agent",
            status="skeleton_ready",
            capabilities=[
                "Agent 配置管理",
                "模型与知识库绑定",
                "工具集合编排",
            ],
        )

    async def list_agents(
        self,
        params: AgentListParams,
    ) -> PageResult[AgentSummaryResp]:
        """Return paginated agent summaries for the admin page."""
        filters = [Agent.deleted_at.is_(None)]
        if params.keyword:
            keyword = f"%{params.keyword.strip()}%"
            filters.append(
                or_(
                    Agent.name.ilike(keyword),
                    Agent.description.ilike(keyword),
                )
            )
        if params.status:
            filters.append(Agent.status == params.status)
        else:
            filters.append(Agent.status != "archived")
        if params.orchestration_mode:
            filters.append(
                Agent.orchestration_mode == params.orchestration_mode
            )
        if params.provider_model_id:
            filters.append(Agent.provider_model_id == params.provider_model_id)

        total_statement = select(func.count()).select_from(Agent).where(
            *filters
        )
        total = int((await self.db.execute(total_statement)).scalar_one())

        statement = (
            select(Agent)
            .where(*filters)
            .options(
                selectinload(Agent.tool_bindings),
                selectinload(Agent.knowledge_bindings),
            )
            .order_by(Agent.id.desc())
            .offset(params.offset)
            .limit(params.page_size)
        )
        agents = list((await self.db.scalars(statement)).all())
        model_map = await self._load_model_summaries(
            [agent.provider_model_id for agent in agents]
        )
        items = [
            self._build_summary_response(agent, model_map=model_map)
            for agent in agents
        ]
        return PageResult.create(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_agent(self, agent_id: int) -> AgentDetailResp:
        """Return one agent detail payload."""
        agent = await self._get_agent_or_raise(agent_id)
        model_map = await self._load_model_summaries([agent.provider_model_id])
        return self._build_detail_response(agent, model_map=model_map)

    async def create_agent(
        self,
        payload: AgentAdminCreateReq,
    ) -> AgentDetailResp:
        """Create an aggregated agent configuration."""
        await self._validate_payload(payload)
        await self._ensure_name_unique(payload.name)

        agent = Agent(
            name=payload.name,
            description=payload.description,
            avatar_url=payload.avatar_url,
            status=payload.status,
            orchestration_mode=payload.orchestration_mode,
            provider_instance_id=payload.provider_instance_id,
            provider_model_id=payload.provider_model_id,
            system_prompt=payload.system_prompt,
            opening_message=payload.opening_message,
            model_config_json=payload.model_settings,
            runtime_config_json=payload.runtime_config,
            workflow_ref_json=payload.workflow_ref,
            tags_json=payload.tags,
            metadata_json=payload.metadata,
        )
        self.db.add(agent)
        await self.db.flush()

        self.db.add_all(
            [
                self._build_tool_binding(agent.id, item)
                for item in payload.tools
            ]
        )
        self.db.add_all(
            [
                self._build_knowledge_binding(agent.id, item)
                for item in payload.knowledge_bases
            ]
        )

        await self.db.commit()
        return await self.get_agent(agent.id)

    async def update_agent(
        self,
        agent_id: int,
        payload: AgentAdminUpdateReq,
    ) -> AgentDetailResp:
        """Update an aggregated agent configuration."""
        agent = await self._get_agent_or_raise(agent_id)
        await self._validate_payload(payload)
        await self._ensure_name_unique(payload.name, exclude_id=agent_id)

        agent.name = payload.name
        agent.description = payload.description
        agent.avatar_url = payload.avatar_url
        agent.status = payload.status
        agent.orchestration_mode = payload.orchestration_mode
        agent.provider_instance_id = payload.provider_instance_id
        agent.provider_model_id = payload.provider_model_id
        agent.system_prompt = payload.system_prompt
        agent.opening_message = payload.opening_message
        agent.model_config_json = payload.model_settings
        agent.runtime_config_json = payload.runtime_config
        agent.workflow_ref_json = payload.workflow_ref
        agent.tags_json = payload.tags
        agent.metadata_json = payload.metadata
        agent.version += 1

        await self._replace_tool_bindings(agent, payload.tools)
        await self._replace_knowledge_bindings(
            agent,
            payload.knowledge_bases,
        )

        await self.db.commit()
        return await self.get_agent(agent_id)

    async def delete_agent(self, agent_id: int) -> None:
        """Soft-delete one agent and its bindings."""
        agent = await self._get_agent_or_raise(agent_id)

        for binding in self._active_tool_bindings(agent):
            binding.soft_delete()
            binding.version += 1

        for binding in self._active_knowledge_bindings(agent):
            binding.soft_delete()
            binding.version += 1

        agent.soft_delete()
        agent.version += 1
        await self.db.commit()

    async def get_agent_config_preview(
        self,
        agent_id: int,
    ) -> AgentRuntimePreviewResp:
        """Return a UI-safe preview of the agent runtime configuration."""
        agent = await self._get_agent_or_raise(agent_id)
        model_map = await self._load_model_summaries([agent.provider_model_id])
        model = (
            model_map.get(agent.provider_model_id)
            if agent.provider_model_id is not None
            else None
        )
        warnings = self._build_preview_warnings(agent, model)
        return AgentRuntimePreviewResp(
            agentId=agent.id,
            name=agent.name,
            status=agent.status,
            orchestrationMode=agent.orchestration_mode,
            isRunnable=not warnings and agent.status == "active",
            model=model,
            enabledToolIds=[
                binding.tool_id
                for binding in self._active_tool_bindings(agent)
                if binding.is_enabled
            ],
            enabledKnowledgeBaseIds=[
                binding.knowledge_base_id
                for binding in self._active_knowledge_bindings(agent)
                if binding.is_enabled
            ],
            runtimeConfig=agent.runtime_config_json,
            workflowRef=agent.workflow_ref_json,
            warnings=warnings,
        )

    async def _get_agent_or_raise(self, agent_id: int) -> Agent:
        statement = (
            select(Agent)
            .where(Agent.id == agent_id, Agent.deleted_at.is_(None))
            .options(
                selectinload(Agent.tool_bindings),
                selectinload(Agent.knowledge_bindings),
            )
        )
        agent = await self.db.scalar(statement)
        if agent is None:
            raise BizException(
                code=AgentErrorCode.AGENT_NOT_FOUND,
                message="Agent 不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return agent

    async def _ensure_name_unique(
        self,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> None:
        statement = select(Agent).where(
            Agent.name == name,
            Agent.deleted_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(Agent.id != exclude_id)
        existed = await self.db.scalar(statement)
        if existed is not None:
            raise BizException(
                code=CommonErrorCode.RESOURCE_ALREADY_EXISTS,
                message="Agent 名称已存在",
                http_status=status.HTTP_409_CONFLICT,
            )

    async def _validate_payload(
        self,
        payload: AgentAdminCreateReq | AgentAdminUpdateReq,
    ) -> None:
        if (
            payload.orchestration_mode == "workflow"
            and payload.status == "active"
        ):
            raise BizException(
                code=AgentErrorCode.INVALID_CONFIGURATION,
                message="Workflow 模块完成前不能启用 Workflow Agent",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if payload.status == "active" and payload.provider_model_id is None:
            raise BizException(
                code=AgentErrorCode.INVALID_CONFIGURATION,
                message="启用 Agent 前必须选择有效模型",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if payload.provider_model_id is not None:
            model_map = await self._load_model_summaries(
                [payload.provider_model_id]
            )
            if payload.provider_model_id not in model_map:
                raise BizException(
                    code=AgentErrorCode.MODEL_NOT_FOUND,
                    message="目标模型不存在或已删除",
                    http_status=status.HTTP_404_NOT_FOUND,
                )

        await self._validate_tool_bindings(payload.tools)

    async def _validate_tool_bindings(
        self,
        bindings: list[AgentToolBindingInput],
    ) -> None:
        enabled_tool_ids = sorted(
            {binding.tool_id for binding in bindings if binding.is_enabled}
        )
        if not enabled_tool_ids:
            return

        statement = select(Tool.id, Tool.status).where(
            Tool.id.in_(enabled_tool_ids),
            Tool.deleted_at.is_(None),
        )
        rows = list((await self.db.execute(statement)).all())
        status_by_id = {
            int(tool_id): status_value for tool_id, status_value in rows
        }
        missing_ids = [
            tool_id
            for tool_id in enabled_tool_ids
            if tool_id not in status_by_id
        ]
        if missing_ids:
            raise BizException(
                code=AgentErrorCode.TOOL_NOT_FOUND,
                message="绑定工具不存在或已删除",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        unavailable_ids = [
            tool_id
            for tool_id, status_value in status_by_id.items()
            if status_value != "enabled"
        ]
        if unavailable_ids:
            raise BizException(
                code=AgentErrorCode.INVALID_CONFIGURATION,
                message="只能绑定已启用的工具",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

    async def _load_model_summaries(
        self,
        model_ids: list[int | None],
    ) -> dict[int, AgentModelSummaryResp]:
        ids = sorted({model_id for model_id in model_ids if model_id})
        if not ids:
            return {}

        statement = text(
            """
            SELECT
                pm.id AS model_id,
                pm.provider_instance_id AS provider_instance_id,
                pm.model_name AS model_name,
                pm.display_name AS display_name,
                pi.name AS provider_name,
                pi.provider_type AS provider_type
            FROM provider_models pm
            LEFT JOIN provider_instances pi
                ON pi.id = pm.provider_instance_id
                AND pi.deleted_at IS NULL
            WHERE pm.id IN :model_ids
                AND pm.deleted_at IS NULL
            """
        ).bindparams(bindparam("model_ids", expanding=True))
        rows = (await self.db.execute(statement, {"model_ids": ids})).mappings()
        return {
            int(row["model_id"]): AgentModelSummaryResp(
                providerInstanceId=int(row["provider_instance_id"]),
                providerName=row["provider_name"],
                providerType=row["provider_type"],
                modelId=int(row["model_id"]),
                modelName=row["model_name"],
                displayName=row["display_name"],
            )
            for row in rows
        }

    async def _replace_tool_bindings(
        self,
        agent: Agent,
        bindings: list[AgentToolBindingInput],
    ) -> None:
        for binding in self._active_tool_bindings(agent):
            binding.soft_delete()
            binding.version += 1
        await self.db.flush()
        self.db.add_all(
            [self._build_tool_binding(agent.id, item) for item in bindings]
        )

    async def _replace_knowledge_bindings(
        self,
        agent: Agent,
        bindings: list[AgentKnowledgeBindingInput],
    ) -> None:
        for binding in self._active_knowledge_bindings(agent):
            binding.soft_delete()
            binding.version += 1
        await self.db.flush()
        self.db.add_all(
            [
                self._build_knowledge_binding(agent.id, item)
                for item in bindings
            ]
        )

    def _build_tool_binding(
        self,
        agent_id: int,
        item: AgentToolBindingInput,
    ) -> AgentToolBinding:
        return AgentToolBinding(
            agent_id=agent_id,
            tool_id=item.tool_id,
            binding_name=item.binding_name,
            is_enabled=item.is_enabled,
            sort_order=item.sort_order,
            config_json=item.config,
            metadata_json=item.metadata,
        )

    def _build_knowledge_binding(
        self,
        agent_id: int,
        item: AgentKnowledgeBindingInput,
    ) -> AgentKnowledgeBinding:
        return AgentKnowledgeBinding(
            agent_id=agent_id,
            knowledge_base_id=item.knowledge_base_id,
            is_enabled=item.is_enabled,
            sort_order=item.sort_order,
            retrieval_config_json=item.retrieval_config,
            metadata_json=item.metadata,
        )

    def _build_summary_response(
        self,
        agent: Agent,
        *,
        model_map: dict[int, AgentModelSummaryResp],
    ) -> AgentSummaryResp:
        return AgentSummaryResp(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            avatarUrl=agent.avatar_url,
            status=agent.status,
            orchestrationMode=agent.orchestration_mode,
            providerInstanceId=agent.provider_instance_id,
            providerModelId=agent.provider_model_id,
            model=(
                model_map.get(agent.provider_model_id)
                if agent.provider_model_id is not None
                else None
            ),
            toolCount=len(self._active_tool_bindings(agent)),
            knowledgeBaseCount=len(self._active_knowledge_bindings(agent)),
            tags=agent.tags_json or [],
            createdAt=agent.created_at,
            updatedAt=agent.updated_at,
        )

    def _build_detail_response(
        self,
        agent: Agent,
        *,
        model_map: dict[int, AgentModelSummaryResp],
    ) -> AgentDetailResp:
        summary = self._build_summary_response(agent, model_map=model_map)
        return AgentDetailResp(
            **summary.model_dump(by_alias=True),
            systemPrompt=agent.system_prompt,
            openingMessage=agent.opening_message,
            modelConfig=agent.model_config_json,
            runtimeConfig=agent.runtime_config_json,
            workflowRef=agent.workflow_ref_json,
            tools=[
                self._build_tool_binding_response(binding)
                for binding in self._active_tool_bindings(agent)
            ],
            knowledgeBases=[
                self._build_knowledge_binding_response(binding)
                for binding in self._active_knowledge_bindings(agent)
            ],
            metadata=agent.metadata_json,
        )

    def _build_tool_binding_response(
        self,
        binding: AgentToolBinding,
    ) -> AgentToolBindingResp:
        return AgentToolBindingResp(
            toolId=binding.tool_id,
            bindingName=binding.binding_name,
            isEnabled=binding.is_enabled,
            sortOrder=binding.sort_order,
            config=binding.config_json,
            metadata=binding.metadata_json,
        )

    def _build_knowledge_binding_response(
        self,
        binding: AgentKnowledgeBinding,
    ) -> AgentKnowledgeBindingResp:
        return AgentKnowledgeBindingResp(
            knowledgeBaseId=binding.knowledge_base_id,
            isEnabled=binding.is_enabled,
            sortOrder=binding.sort_order,
            retrievalConfig=binding.retrieval_config_json,
            metadata=binding.metadata_json,
        )

    def _build_preview_warnings(
        self,
        agent: Agent,
        model: AgentModelSummaryResp | None,
    ) -> list[str]:
        warnings: list[str] = []
        if agent.status != "active":
            warnings.append("Agent 当前不是启用状态")
        if model is None:
            warnings.append("Agent 尚未绑定有效模型")
        if agent.orchestration_mode == "workflow":
            warnings.append("Workflow 编排尚未启用")
        return warnings

    def _active_tool_bindings(self, agent: Agent) -> list[AgentToolBinding]:
        return sorted(
            [
                binding
                for binding in agent.tool_bindings
                if binding.deleted_at is None
            ],
            key=lambda item: (item.sort_order, item.id),
        )

    def _active_knowledge_bindings(
        self,
        agent: Agent,
    ) -> list[AgentKnowledgeBinding]:
        return sorted(
            [
                binding
                for binding in agent.knowledge_bindings
                if binding.deleted_at is None
            ],
            key=lambda item: (item.sort_order, item.id),
        )
