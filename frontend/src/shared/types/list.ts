import type { ReactNode } from "react";
import type { ColumnType } from "antd/es/table";

export interface PageResult<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export type ListRequestParams<TQuery extends object> = TQuery & {
  page: number;
  pageSize: number;
};

export interface ListSelectOption {
  label: ReactNode;
  value: string | number;
}

interface ListFilterFieldBase {
  label: ReactNode;
  placeholder?: string;
}

export interface ListInputFilterField extends ListFilterFieldBase {
  type: "input";
  key: string;
  allowClear?: boolean;
}

export interface ListSelectFilterField extends ListFilterFieldBase {
  type: "select";
  key: string;
  options: ListSelectOption[];
  allowClear?: boolean;
}

export interface ListDateRangeFilterField extends ListFilterFieldBase {
  type: "dateRange";
  key: string;
  queryKeys: [string, string];
}

export interface ListCustomFilterFieldRenderContext {
  value: unknown;
  onChange: (value: unknown) => void;
  formValues: Record<string, unknown>;
}

export interface ListCustomFilterField extends ListFilterFieldBase {
  type: "custom";
  key: string;
  render: (context: ListCustomFilterFieldRenderContext) => ReactNode;
}

export type ListFilterField =
  | ListInputFilterField
  | ListSelectFilterField
  | ListDateRangeFilterField
  | ListCustomFilterField;

export type ListTableColumn<TData> = ColumnType<TData> & {
  label?: ReactNode;
  prop?: Extract<keyof TData, string | number> | string;
  slot?: (record: TData, index: number) => ReactNode;
};

export interface BatchActionContext<TData> {
  selectedRowKeys: React.Key[];
  selectedRows: TData[];
  clearSelection: () => void;
}

export interface ListTableRef<TData> {
  reload: () => void;
  reset: () => void;
  clearSelection: () => void;
  getSelectedRows: () => TData[];
}
