import type { ReactNode } from "react";
import type { ColProps, RowProps } from "antd";
import type { QueryKey } from "@tanstack/react-query";
import type { Rule } from "antd/es/form";

export type FormDialogMode = "create" | "edit";

export interface FormDialogOption {
  label: ReactNode;
  value: string | number | boolean;
}

interface FormDialogFieldBase {
  key: string;
  label: ReactNode;
  required?: boolean;
  placeholder?: string;
  rules?: Rule[];
  hidden?: boolean;
  disabled?: boolean;
  colProps?: ColProps;
}

export interface FormDialogInputField extends FormDialogFieldBase {
  type: "input";
  allowClear?: boolean;
}

export interface FormDialogTextareaField extends FormDialogFieldBase {
  type: "textarea";
  rows?: number;
}

export interface FormDialogSelectField extends FormDialogFieldBase {
  type: "select";
  options: FormDialogOption[];
  allowClear?: boolean;
}

export interface FormDialogDatePickerField extends FormDialogFieldBase {
  type: "datePicker";
}

export interface FormDialogDateRangeField extends FormDialogFieldBase {
  type: "dateRange";
}

export interface FormDialogSwitchField extends FormDialogFieldBase {
  type: "switch";
  checkedChildren?: ReactNode;
  unCheckedChildren?: ReactNode;
}

export interface FormDialogCustomFieldRenderContext {
  value: unknown;
  onChange: (value: unknown) => void;
  formValues: Record<string, unknown>;
  mode: FormDialogMode;
}

export interface FormDialogCustomField extends FormDialogFieldBase {
  type: "custom";
  render: (context: FormDialogCustomFieldRenderContext) => ReactNode;
}

export type FormDialogField =
  | FormDialogInputField
  | FormDialogTextareaField
  | FormDialogSelectField
  | FormDialogDatePickerField
  | FormDialogDateRangeField
  | FormDialogSwitchField
  | FormDialogCustomField;

export interface FormDialogSubmitContext<TDetail> {
  mode: FormDialogMode;
  editId?: string | number;
  detailData?: TDetail;
}

export interface SubmitActionConfig<TValues, TDetail> {
  text: string;
  mutationKey?: (context: FormDialogSubmitContext<TDetail>) => QueryKey;
  mapValues?: (values: TValues) => unknown;
  api: (
    values: unknown,
    context: FormDialogSubmitContext<TDetail>,
    signal?: AbortSignal,
  ) => Promise<unknown>;
  closeOnSuccess?: boolean;
  resetOnSuccess?: boolean;
  successMessage?: string;
}

export interface FormDialogLayoutProps {
  rowProps?: RowProps;
  defaultColProps?: ColProps;
}
