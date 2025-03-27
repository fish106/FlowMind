import { API_URL, RUN_URL } from '@/lib/constants';
import { hashFile } from '@/lib/hash';
import { TaskID, TaskSchemaID, TenantID } from '@/types/aliases';
import { JsonSchema } from '@/types/json_schema';
import { FieldQuery } from '@/types/workflowAI';

export function buildScopeKey({
  tenant,
  taskId,
  taskSchemaId,
  searchParams,
}: {
  tenant: TenantID | undefined;
  taskId: TaskID;
  taskSchemaId?: string;
  searchParams?: string;
}) {
  return `${tenant}-${taskId}-${taskSchemaId}-${searchParams}`;
}

export function buildVersionScopeKey({
  tenant,
  taskId,
  versionId,
}: {
  tenant: TenantID | undefined;
  taskId: TaskID;
  versionId: string | undefined;
}) {
  return `${tenant}-${taskId}-${versionId}`;
}

export function buildSearchTaskRunsScopeKey({
  tenant,
  taskId,
  limit,
  offset,
  fieldQueries,
}: {
  tenant: TenantID | undefined;
  taskId: TaskID;
  taskSchemaId?: string;
  limit: number;
  offset: number;
  fieldQueries: Array<FieldQuery> | undefined;
}) {
  let result = `${tenant}-${taskId}-${limit}-${offset}`;
  if (fieldQueries) {
    result += `-${fieldQueries
      .map((query) => `${query.field_name}-${query.operator}-${query.values.join(',')}`)
      .join(',')}`;
  }
  return result;
}

export function buildTaskStatsScopeKey({
  tenant,
  taskId,
  createdAfter,
  createdBefore,
  taskSchemaId,
  version,
  isActive,
}: {
  tenant: TenantID | undefined;
  taskId: TaskID;
  createdAfter?: Date;
  createdBefore?: Date;
  taskSchemaId?: TaskSchemaID;
  version?: number;
  isActive?: boolean;
}) {
  return `${tenant}-${taskId}-${createdAfter}-${createdBefore}-${taskSchemaId}-${version}-${isActive}`;
}

export function rootTenantPath(tenant?: TenantID | undefined, v1: boolean = false) {
  return `/api/data/${v1 ? 'v1/' : ''}${tenant ?? '_'}`;
}

// "_" is a special tenant that is equivalent to the tenant provided in the JWT
export function rootTaskPath(tenant?: TenantID | undefined, v1: boolean = false) {
  return `${rootTenantPath(tenant, v1)}/agents`;
}

export function taskSubPath(tenant: TenantID | undefined, taskId: TaskID, subpath: string, v1: boolean = false) {
  return `${rootTaskPath(tenant, v1)}/${taskId}${subpath}`;
}

export function taskSchemaSubPath(
  tenant: TenantID | undefined,
  taskId: TaskID,
  taskSchemaId: number | string,
  subpath: string,
  v1: boolean = false
) {
  return `${rootTaskPath(tenant, v1)}/${taskId}/schemas/${taskSchemaId}${subpath}`;
}

export function rootTaskPathNoProxy(tenant?: TenantID) {
  return `${API_URL}/${tenant ?? '_'}/agents`;
}

export function rootTaskPathNoProxyV1(tenant?: TenantID) {
  return `${API_URL}/v1/${tenant ?? '_'}/agents`;
}

export function runTaskPathNoProxy(tenant?: TenantID) {
  return `${RUN_URL}/v1/${tenant ?? '_'}/agents`;
}

export function getOrUndef<T>(map: Map<string, T>, key: string | undefined) {
  return key ? map.get(key) : undefined;
}

function hashSchema(schema: JsonSchema) {
  return hashFile(JSON.stringify(schema));
}

export function buildTaskPreviewScopeKey({
  inputSchema,
  outputSchema,
}: {
  inputSchema: Record<string, unknown> | undefined;
  outputSchema: Record<string, unknown> | undefined;
}) {
  const inputHash = inputSchema ? hashSchema(inputSchema) : undefined;
  const outputHash = outputSchema ? hashSchema(outputSchema) : undefined;
  return `${inputHash}-${outputHash}`;
}
