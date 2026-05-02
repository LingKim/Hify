import { useEffect, useRef, useState, type ReactNode } from "react";
import { App, Button, Col, DatePicker, Form, Input, Modal, Row, Select, Space, Spin, Switch } from "antd";
import { FullscreenExitOutlined, FullscreenOutlined } from "@ant-design/icons";
import { useMutation, useQuery, type QueryKey } from "@tanstack/react-query";
import type { ColProps, RowProps } from "antd";
import { getErrorMessage } from "@/shared/api";
import type {
  FormDialogField,
  FormDialogLayoutProps,
  FormDialogMode,
  FormDialogSubmitContext,
  SubmitActionConfig,
} from "@/shared/types/form-dialog";

const DEFAULT_COL_PROPS = {
  xs: 24,
  md: 12,
} as const;

const DEFAULT_ROW_GUTTER: NonNullable<RowProps["gutter"]> = [16, 0];

export interface FormDialogProps<TValues extends object, TDetail = TValues>
  extends FormDialogLayoutProps {
  open: boolean;
  mode: FormDialogMode;
  title?: ReactNode | ((mode: FormDialogMode) => ReactNode);
  width?: number | string;
  onOpenChange?: (open: boolean) => void;
  onClose?: () => void;
  fullscreen?: boolean;
  schema: FormDialogField[];
  initialValues?: Partial<TValues>;
  layout?: "vertical" | "horizontal";
  disabled?: boolean;
  editId?: string | number;
  detailQueryKey?: (id: string | number) => QueryKey;
  detailApi?: (id: string | number, signal?: AbortSignal) => Promise<TDetail>;
  mapDetailToValues?: (detail: TDetail) => Partial<TValues>;
  primaryAction: SubmitActionConfig<TValues, TDetail>;
  secondaryAction?: SubmitActionConfig<TValues, TDetail>;
  onSuccess?: (
    result: unknown,
    context: FormDialogSubmitContext<TDetail>,
  ) => void | Promise<void>;
}

function normalizeValues<TValues extends object>(
  values: Partial<TValues> | undefined,
): Partial<TValues> {
  if (values === undefined) {
    return {};
  }

  return Object.fromEntries(
    Object.entries(values as Record<string, unknown>).filter(([, value]) => value !== undefined),
  ) as Partial<TValues>;
}

function buildFieldRules(field: FormDialogField): ReturnType<typeof Form.Item>["props"]["rules"] {
  if (field.required !== true) {
    return field.rules;
  }

  const requiredMessage =
    field.type === "select" || field.type === "datePicker" || field.type === "dateRange"
      ? `请选择${field.label}`
      : `请输入${field.label}`;

  return [
    {
      required: true,
      message: requiredMessage,
    },
    ...(field.rules ?? []),
  ];
}

export function FormDialog<TValues extends object, TDetail = TValues>({
  open,
  mode,
  title,
  width = 720,
  onOpenChange,
  onClose,
  fullscreen = false,
  schema,
  initialValues,
  layout = "vertical",
  disabled = false,
  editId,
  detailQueryKey,
  detailApi,
  mapDetailToValues,
  rowProps,
  defaultColProps,
  primaryAction,
  secondaryAction,
  onSuccess,
}: FormDialogProps<TValues, TDetail>): JSX.Element {
  const [form] = Form.useForm<TValues>();
  const { message } = App.useApp();
  const [isFullscreen, setIsFullscreen] = useState(fullscreen);
  const baselineValuesRef = useRef<Partial<TValues>>({});
  const primaryAbortControllerRef = useRef<AbortController | null>(null);
  const secondaryAbortControllerRef = useRef<AbortController | null>(null);

  const buildSubmitContext = (detailData?: TDetail): FormDialogSubmitContext<TDetail> => ({
    mode,
    editId,
    detailData,
  });

  const detailQuery = useQuery({
    queryKey:
      mode === "edit" && editId !== undefined
        ? detailQueryKey?.(editId) ?? ["form-dialog-detail", editId]
        : ["form-dialog-detail-idle"],
    queryFn: ({ signal }) => {
      if (detailApi === undefined || editId === undefined) {
        throw new Error("detailApi is not available");
      }

      return detailApi(editId, signal);
    },
    enabled: open && mode === "edit" && detailApi !== undefined && editId !== undefined,
    retry: false,
  });

  const applyBaselineValues = (values: Partial<TValues>) => {
    baselineValuesRef.current = values;
    form.resetFields();
    form.setFieldsValue(values as Parameters<typeof form.setFieldsValue>[0]);
  };

  useEffect(() => {
    if (!open) {
      setIsFullscreen(fullscreen);
      primaryAbortControllerRef.current?.abort();
      secondaryAbortControllerRef.current?.abort();
      form.resetFields();
      return;
    }

    applyBaselineValues(normalizeValues(initialValues));
  }, [open, mode, editId, initialValues, fullscreen, form]);

  useEffect(() => {
    if (!open || mode !== "edit" || detailQuery.data === undefined) {
      return;
    }

    const mappedDetailValues =
      mapDetailToValues?.(detailQuery.data) ??
      (detailQuery.data as unknown as Partial<TValues>);
    const mergedValues = {
      ...normalizeValues(initialValues),
      ...normalizeValues(mappedDetailValues),
    };

    applyBaselineValues(mergedValues);
  }, [open, mode, initialValues, detailQuery.data, mapDetailToValues, form]);

  useEffect(() => {
    return () => {
      primaryAbortControllerRef.current?.abort();
      secondaryAbortControllerRef.current?.abort();
    };
  }, []);

  const primaryMutation = useMutation({
    mutationKey: primaryAction.mutationKey?.(buildSubmitContext(detailQuery.data)),
    mutationFn: async () => {
      const values = await form.validateFields();
      primaryAbortControllerRef.current?.abort();
      const controller = new AbortController();
      primaryAbortControllerRef.current = controller;
      const payload = primaryAction.mapValues?.(values) ?? values;
      return primaryAction.api(
        payload,
        buildSubmitContext(detailQuery.data),
        controller.signal,
      );
    },
    onSuccess: async (result) => {
      if (primaryAction.successMessage !== undefined) {
        message.success(primaryAction.successMessage);
      }

      await onSuccess?.(result, buildSubmitContext(detailQuery.data));

      if (primaryAction.resetOnSuccess === true) {
        applyBaselineValues(baselineValuesRef.current);
      }

      if (primaryAction.closeOnSuccess !== false) {
        onOpenChange?.(false);
        onClose?.();
      }
    },
  });

  const secondaryMutation = useMutation({
    mutationKey: secondaryAction?.mutationKey?.(buildSubmitContext(detailQuery.data)),
    mutationFn: async () => {
      if (secondaryAction === undefined) {
        throw new Error("secondaryAction is not configured");
      }

      const values = await form.validateFields();
      secondaryAbortControllerRef.current?.abort();
      const controller = new AbortController();
      secondaryAbortControllerRef.current = controller;
      const payload = secondaryAction.mapValues?.(values) ?? values;
      return secondaryAction.api(
        payload,
        buildSubmitContext(detailQuery.data),
        controller.signal,
      );
    },
    onSuccess: async (result) => {
      if (secondaryAction?.successMessage !== undefined) {
        message.success(secondaryAction.successMessage);
      }

      await onSuccess?.(result, buildSubmitContext(detailQuery.data));

      if (secondaryAction?.resetOnSuccess === true) {
        applyBaselineValues(baselineValuesRef.current);
      }

      if (secondaryAction?.closeOnSuccess === true) {
        onOpenChange?.(false);
        onClose?.();
      }
    },
  });

  const currentFormValues = form.getFieldsValue(true) as Record<string, unknown>;
  const resolvedTitle = typeof title === "function" ? title(mode) : title;
  const resolvedRowProps: RowProps = rowProps ?? { gutter: DEFAULT_ROW_GUTTER };
  const resolvedDefaultColProps: ColProps = defaultColProps ?? DEFAULT_COL_PROPS;

  return (
    <Modal
      open={open}
      width={isFullscreen ? "calc(100vw - 48px)" : width}
      onCancel={() => {
        onOpenChange?.(false);
        onClose?.();
      }}
      className={`form-dialog-modal${isFullscreen ? " form-dialog-modal-fullscreen" : ""}`}
      title={
        <div className="form-dialog-titlebar">
          <div className="form-dialog-title">{resolvedTitle}</div>
          <Button
            type="text"
            size="small"
            aria-label={isFullscreen ? "退出全屏" : "放大全屏"}
            icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
            onClick={() => setIsFullscreen((currentValue) => !currentValue)}
          />
        </div>
      }
      footer={
        <Space size={8}>
          <Button
            onClick={() => {
              onOpenChange?.(false);
              onClose?.();
            }}
          >
            取消
          </Button>
          {secondaryAction !== undefined ? (
            <Button
              loading={secondaryMutation.isPending}
              disabled={primaryMutation.isPending}
              onClick={() => void secondaryMutation.mutateAsync()}
            >
              {secondaryAction.text}
            </Button>
          ) : null}
          <Button
            type="primary"
            loading={primaryMutation.isPending}
            disabled={secondaryMutation.isPending}
            onClick={() => void primaryMutation.mutateAsync()}
          >
            {primaryAction.text}
          </Button>
        </Space>
      }
      destroyOnHidden={false}
    >
      {detailQuery.isError ? (
        <div className="form-dialog-error">
          {getErrorMessage(detailQuery.error)}
        </div>
      ) : null}

      <Spin spinning={detailQuery.isFetching}>
        <Form form={form} layout={layout} disabled={disabled}>
          <Row {...resolvedRowProps}>
            {schema
              .filter((field) => field.hidden !== true)
              .map((field) => {
                const colProps = field.colProps ?? resolvedDefaultColProps;
                const fieldDisabled = disabled || field.disabled === true;

                return (
                  <Col
                    key={field.key}
                    {...colProps}
                    data-testid={`form-dialog-col-${field.key}`}
                  >
                    <Form.Item
                      name={field.key}
                      label={field.label}
                      rules={buildFieldRules(field)}
                      valuePropName={field.type === "switch" ? "checked" : "value"}
                    >
                      {renderField(
                        field,
                        fieldDisabled,
                        currentFormValues,
                        mode,
                        (value) => {
                          form.setFieldValue(field.key as never, value);
                        },
                      )}
                    </Form.Item>
                  </Col>
                );
              })}
          </Row>
        </Form>
      </Spin>
    </Modal>
  );
}

function renderField(
  field: FormDialogField,
  disabled: boolean,
  formValues: Record<string, unknown>,
  mode: FormDialogMode,
  onCustomChange: (value: unknown) => void,
): ReactNode {
  if (field.type === "input") {
    return (
      <Input
        allowClear={field.allowClear ?? true}
        placeholder={field.placeholder}
        disabled={disabled}
      />
    );
  }

  if (field.type === "textarea") {
    return (
      <Input.TextArea
        rows={field.rows ?? 4}
        placeholder={field.placeholder}
        disabled={disabled}
      />
    );
  }

  if (field.type === "select") {
    return (
      <Select
        allowClear={field.allowClear ?? true}
        placeholder={field.placeholder}
        options={field.options}
        disabled={disabled}
      />
    );
  }

  if (field.type === "datePicker") {
    return <DatePicker style={{ width: "100%" }} disabled={disabled} />;
  }

  if (field.type === "dateRange") {
    return <DatePicker.RangePicker style={{ width: "100%" }} disabled={disabled} />;
  }

  if (field.type === "switch") {
    return (
      <Switch
        checkedChildren={field.checkedChildren}
        unCheckedChildren={field.unCheckedChildren}
        disabled={disabled}
      />
    );
  }

  return field.render({
    value: formValues[field.key],
    onChange: onCustomChange,
    formValues,
    mode,
  });
}
