SHELL := /bin/bash

ROOT_DIR := $(CURDIR)
FRONTEND_DIR := $(ROOT_DIR)/frontend
BACKEND_DIR := $(ROOT_DIR)/backend
RUN_DIR := $(ROOT_DIR)/.run
DIST_DIR := $(ROOT_DIR)/dist
PACKAGE_STAGE_DIR := $(DIST_DIR)/package
FRONTEND_PID_FILE := $(RUN_DIR)/frontend.pid
BACKEND_PID_FILE := $(RUN_DIR)/backend.pid
FRONTEND_PORT_FILE := $(RUN_DIR)/frontend.port
BACKEND_PORT_FILE := $(RUN_DIR)/backend.port
FRONTEND_LOG_FILE := $(RUN_DIR)/frontend.log
BACKEND_LOG_FILE := $(RUN_DIR)/backend.log

FRONTEND_HOST ?= 127.0.0.1
FRONTEND_PORT ?= 5173
BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000

FRONTEND_URL := http://$(FRONTEND_HOST):$(FRONTEND_PORT)
BACKEND_URL := http://$(BACKEND_HOST):$(BACKEND_PORT)
BACKEND_HEALTH_URL := $(BACKEND_URL)/api/v1/health
VERSION := $(shell sed -n 's/^version = "\(.*\)"/\1/p' $(BACKEND_DIR)/pyproject.toml | head -n 1)
PACKAGE_NAME := hify-$(VERSION)
PACKAGE_ROOT := $(PACKAGE_STAGE_DIR)/$(PACKAGE_NAME)
PACKAGE_ARCHIVE := $(DIST_DIR)/$(PACKAGE_NAME).tar.gz

.PHONY: start stop restart build clean package

start:
	@set -euo pipefail; \
	mkdir -p "$(RUN_DIR)"; \
	for command_name in pnpm uv curl lsof; do \
		if ! command -v "$$command_name" >/dev/null 2>&1; then \
			echo "缺少命令: $$command_name"; \
			exit 1; \
		fi; \
	done; \
	for pid_file in "$(FRONTEND_PID_FILE)" "$(BACKEND_PID_FILE)"; do \
		if [[ -f "$$pid_file" ]] && ! kill -0 "$$(cat "$$pid_file")" 2>/dev/null; then \
			rm -f "$$pid_file"; \
		fi; \
	done; \
	if [[ -f "$(FRONTEND_PID_FILE)" ]] || [[ -f "$(BACKEND_PID_FILE)" ]]; then \
		echo "检测到服务可能已在运行，请先执行 make stop。"; \
		exit 1; \
	fi; \
	if command -v lsof >/dev/null 2>&1; then \
		for port in "$(BACKEND_PORT)" "$(FRONTEND_PORT)"; do \
			if lsof -ti "tcp:$$port" -sTCP:LISTEN >/dev/null 2>&1; then \
				echo "端口 $$port 已被占用，请先释放端口或使用其他端口启动。"; \
				exit 1; \
			fi; \
		done; \
	fi; \
	if [[ ! -d "$(FRONTEND_DIR)/node_modules" ]]; then \
		echo "前端依赖未安装，正在执行 pnpm install..."; \
		cd "$(FRONTEND_DIR)" && pnpm install; \
	fi; \
	echo "$(BACKEND_PORT)" >"$(BACKEND_PORT_FILE)"; \
	echo "$(FRONTEND_PORT)" >"$(FRONTEND_PORT_FILE)"; \
	echo "启动后端开发服务: $(BACKEND_URL)"; \
	nohup bash -lc 'cd "$(BACKEND_DIR)" && exec uv run uvicorn app.main:app --host "$(BACKEND_HOST)" --port "$(BACKEND_PORT)" --reload' >"$(BACKEND_LOG_FILE)" 2>&1 & \
	backend_launcher_pid="$$!"; \
	echo "启动前端开发服务: $(FRONTEND_URL)"; \
	nohup bash -lc 'cd "$(FRONTEND_DIR)" && exec pnpm dev -- --host "$(FRONTEND_HOST)" --port "$(FRONTEND_PORT)"' >"$(FRONTEND_LOG_FILE)" 2>&1 & \
	frontend_launcher_pid="$$!"; \
	for _ in $$(seq 1 60); do \
		if ! kill -0 "$$backend_launcher_pid" 2>/dev/null && \
		   ! lsof -ti "tcp:$(BACKEND_PORT)" -sTCP:LISTEN >/dev/null 2>&1; then \
			break; \
		fi; \
		if ! kill -0 "$$frontend_launcher_pid" 2>/dev/null && \
		   ! lsof -ti "tcp:$(FRONTEND_PORT)" -sTCP:LISTEN >/dev/null 2>&1; then \
			break; \
		fi; \
		if curl --silent --fail "$(BACKEND_HEALTH_URL)" >/dev/null 2>&1 && \
		   curl --silent --fail "$(FRONTEND_URL)" >/dev/null 2>&1; then \
			break; \
		fi; \
		sleep 1; \
	done; \
	if ! curl --silent --fail "$(BACKEND_HEALTH_URL)" >/dev/null 2>&1 || \
	   ! curl --silent --fail "$(FRONTEND_URL)" >/dev/null 2>&1; then \
		echo "服务启动超时，正在停止已启动进程。"; \
		$(MAKE) stop; \
		if [[ -f "$(BACKEND_LOG_FILE)" ]]; then \
			echo "--- backend.log ---"; \
			tail -n 20 "$(BACKEND_LOG_FILE)" || true; \
		fi; \
		if [[ -f "$(FRONTEND_LOG_FILE)" ]]; then \
			echo "--- frontend.log ---"; \
			tail -n 20 "$(FRONTEND_LOG_FILE)" || true; \
		fi; \
		exit 1; \
	fi; \
	if command -v lsof >/dev/null 2>&1; then \
		lsof -ti "tcp:$(BACKEND_PORT)" -sTCP:LISTEN | sort -u >"$(BACKEND_PID_FILE)"; \
		lsof -ti "tcp:$(FRONTEND_PORT)" -sTCP:LISTEN | sort -u >"$(FRONTEND_PID_FILE)"; \
	fi; \
	if command -v open >/dev/null 2>&1; then \
		open "$(FRONTEND_URL)"; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open "$(FRONTEND_URL)" >/dev/null 2>&1 || true; \
	fi; \
	echo "前端地址: $(FRONTEND_URL)"; \
	echo "后端地址: $(BACKEND_URL)"; \
	echo "日志目录: $(RUN_DIR)"; \
	echo "可使用 make stop 停止服务。"

stop:
	@set -euo pipefail; \
	stopped_any=0; \
	for service in frontend backend; do \
		pid_file="$(RUN_DIR)/$$service.pid"; \
		port_file="$(RUN_DIR)/$$service.port"; \
		port=""; \
		if [[ -f "$$port_file" ]]; then \
			port="$$(cat "$$port_file")"; \
		fi; \
		pid_candidates=""; \
		if [[ -f "$$pid_file" ]]; then \
			pid_candidates="$$(tr '\n' ' ' <"$$pid_file")"; \
		fi; \
		if [[ -n "$$port" ]] && command -v lsof >/dev/null 2>&1; then \
			pid_candidates="$$pid_candidates $$(lsof -ti "tcp:$$port" -sTCP:LISTEN | sort -u | tr '\n' ' ')"; \
		fi; \
		pids="$$(printf '%s\n' $$pid_candidates | tr ' ' '\n' | awk 'NF' | sort -u | tr '\n' ' ')"; \
		if [[ -n "$$pids" ]]; then \
			for pid in $$pids; do \
				if kill -0 "$$pid" 2>/dev/null; then \
					echo "停止 $$service 服务 (PID=$$pid)"; \
					kill "$$pid" 2>/dev/null || true; \
					stopped_any=1; \
				fi; \
			done; \
		fi; \
		if [[ -n "$$pids" ]]; then \
			sleep 1; \
			for pid in $$pids; do \
				if kill -0 "$$pid" 2>/dev/null; then \
					kill -9 "$$pid" 2>/dev/null || true; \
				fi; \
			done; \
		fi; \
		rm -f "$$pid_file" "$$port_file"; \
	done; \
	if [[ "$$stopped_any" -eq 0 ]]; then \
		echo "没有检测到运行中的前后端服务。"; \
	else \
		echo "前后端服务已停止。"; \
	fi

restart:
	@$(MAKE) stop
	@$(MAKE) start

build:
	@set -euo pipefail; \
	echo "构建后端分发产物"; \
	rm -rf "$(BACKEND_DIR)/dist"; \
	cd "$(BACKEND_DIR)" && uv build --out-dir dist; \
	echo "构建前端静态产物"; \
	cd "$(FRONTEND_DIR)" && pnpm build

clean:
	@set -euo pipefail; \
	$(MAKE) stop; \
	rm -rf "$(FRONTEND_DIR)/dist" "$(BACKEND_DIR)/dist" "$(DIST_DIR)" "$(RUN_DIR)"; \
	echo "已清理构建产物与运行目录。"

package: build
	@set -euo pipefail; \
	rm -rf "$(PACKAGE_STAGE_DIR)" "$(PACKAGE_ARCHIVE)"; \
	mkdir -p "$(PACKAGE_ROOT)/backend" "$(PACKAGE_ROOT)/frontend" "$(DIST_DIR)"; \
	cp -R "$(BACKEND_DIR)/app" "$(PACKAGE_ROOT)/backend/app"; \
	cp -R "$(BACKEND_DIR)/alembic" "$(PACKAGE_ROOT)/backend/alembic"; \
	cp -R "$(BACKEND_DIR)/dist" "$(PACKAGE_ROOT)/backend/dist"; \
	cp "$(BACKEND_DIR)/pyproject.toml" "$(PACKAGE_ROOT)/backend/pyproject.toml"; \
	cp "$(BACKEND_DIR)/uv.lock" "$(PACKAGE_ROOT)/backend/uv.lock"; \
	cp "$(BACKEND_DIR)/README.md" "$(PACKAGE_ROOT)/backend/README.md"; \
	cp -R "$(FRONTEND_DIR)/dist" "$(PACKAGE_ROOT)/frontend/dist"; \
	cp "$(FRONTEND_DIR)/package.json" "$(PACKAGE_ROOT)/frontend/package.json"; \
	cp "$(FRONTEND_DIR)/pnpm-lock.yaml" "$(PACKAGE_ROOT)/frontend/pnpm-lock.yaml"; \
	cp "$(ROOT_DIR)/README.md" "$(PACKAGE_ROOT)/README.md"; \
	cp "$(ROOT_DIR)/Makefile" "$(PACKAGE_ROOT)/Makefile"; \
	find "$(PACKAGE_ROOT)" -type d -name "__pycache__" -prune -exec rm -rf {} +; \
	find "$(PACKAGE_ROOT)" -type f \( -name "*.pyc" -o -name ".DS_Store" -o -name ".gitignore" \) -delete; \
	tar -czf "$(PACKAGE_ARCHIVE)" -C "$(PACKAGE_STAGE_DIR)" "$(PACKAGE_NAME)"; \
	echo "打包完成: $(PACKAGE_ARCHIVE)"
