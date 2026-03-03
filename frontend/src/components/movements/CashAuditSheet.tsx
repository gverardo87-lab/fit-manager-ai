"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ExternalLink,
  FileSearch,
  Filter,
  Loader2,
  RotateCcw,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useCashAuditLogInfinite } from "@/hooks/useMovements";
import type { CashAuditTimelineItem } from "@/types/api";

interface CashAuditSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNavigateInCash?: (href: string) => void;
}

type ActionFilter = "ALL" | "CREATE" | "UPDATE" | "DELETE" | "RESTORE";
type EntityFilter = "ALL" | "movement" | "recurring_expense" | "rate" | "contract";
type FlowFilter = "ALL" | "ENTRATA" | "USCITA";
const PAGE_SIZE = 60;

const CASH_PATH = "/cassa";

function isCashInternalHref(href: string): boolean {
  try {
    const url = new URL(href, "https://fitmanager.local");
    return url.pathname === CASH_PATH;
  } catch {
    return false;
  }
}

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderValue(v: unknown): string {
  if (v === null || v === undefined) return "-";
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v === "number") return String(v);
  if (typeof v === "string") return v;
  return JSON.stringify(v);
}

function ActionBadge({ action }: { action: string }) {
  if (action === "DELETE") return <Badge variant="destructive">DELETE</Badge>;
  if (action === "RESTORE") return <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">RESTORE</Badge>;
  if (action === "CREATE") return <Badge className="bg-blue-600 text-white hover:bg-blue-600">CREATE</Badge>;
  return <Badge variant="outline">{action}</Badge>;
}

function AuditRow({
  item,
  onNavigateInCash,
}: {
  item: CashAuditTimelineItem;
  onNavigateInCash?: (href: string) => void;
}) {
  const fields = Object.keys(item.before || {});
  const hasDiff = fields.length > 0;
  const linkHref = item.link_href ?? "";
  const isInternalCashLink = Boolean(
    item.link_href && onNavigateInCash && isCashInternalHref(item.link_href)
  );

  return (
    <div className="rounded-lg border p-3">
      <div className="flex flex-wrap items-center gap-2">
        <ActionBadge action={item.action} />
        <Badge variant="outline">{item.entity_type} #{item.entity_id}</Badge>
        {item.flow_hint && <Badge variant="secondary">{item.flow_hint}</Badge>}
        <span className="ml-auto text-xs text-muted-foreground">
          {formatDateTime(item.created_at)}
        </span>
      </div>

      {item.reason && (
        <p className="mt-2 text-sm">{item.reason}</p>
      )}

      <p className="mt-1 text-xs text-muted-foreground">
        Correlation: <span className="font-mono">{item.correlation_id ?? "-"}</span>
      </p>

      {hasDiff && (
        <div className="mt-2 rounded-md border bg-muted/20 p-2">
          <p className="text-[11px] font-semibold uppercase text-muted-foreground">
            Before {"->"} After
          </p>
          <div className="mt-1 space-y-1">
            {fields.map((field) => (
              <div key={field} className="text-xs">
                <span className="font-medium">{field}</span>:{" "}
                <span className="font-mono">{renderValue(item.before[field])}</span>{" "}
                {"->"}{" "}
                <span className="font-mono">{renderValue(item.after[field])}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {item.link_href && item.link_label && (
        <div className="mt-3">
          <Button asChild variant="outline" size="sm" className="gap-1.5">
            <Link
              href={linkHref}
              onClick={(event) => {
                if (!isInternalCashLink) return;
                event.preventDefault();
                onNavigateInCash?.(linkHref);
              }}
            >
              <ExternalLink className="h-3.5 w-3.5" />
              {item.link_label}
            </Link>
          </Button>
        </div>
      )}
    </div>
  );
}

export function CashAuditSheet({
  open,
  onOpenChange,
  onNavigateInCash,
}: CashAuditSheetProps) {
  const [dataDa, setDataDa] = useState("");
  const [dataA, setDataA] = useState("");
  const [action, setAction] = useState<ActionFilter>("ALL");
  const [entityType, setEntityType] = useState<EntityFilter>("ALL");
  const [flow, setFlow] = useState<FlowFilter>("ALL");

  const {
    data,
    isLoading,
    isFetching,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
    refetch,
  } = useCashAuditLogInfinite(
    {
      data_da: dataDa || undefined,
      data_a: dataA || undefined,
      action: action === "ALL" ? undefined : action,
      entity_type: entityType === "ALL" ? undefined : entityType,
      flow: flow === "ALL" ? undefined : flow,
      pageSize: PAGE_SIZE,
    },
    open
  );

  const resetFilters = () => {
    setDataDa("");
    setDataA("");
    setAction("ALL");
    setEntityType("ALL");
    setFlow("ALL");
  };

  const items = useMemo(
    () => data?.pages.flatMap((page) => page.items) ?? [],
    [data]
  );
  const total = data?.pages[0]?.total ?? 0;
  const isFirstPageLoading = isLoading && items.length === 0;
  const hasMore = Boolean(hasNextPage);
  const isLoadingMore = isFetchingNextPage;
  const handleRefresh = () => refetch();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-hidden sm:max-w-xl">
        <SheetHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-800">
              <FileSearch className="h-5 w-5 text-zinc-700 dark:text-zinc-200" />
            </div>
            <div>
              <SheetTitle>Registro Modifiche Cassa</SheetTitle>
              <SheetDescription>
                Timeline operativa: non sostituisce il libro mastro, lo traccia.
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="space-y-3 border-y px-4 py-3">
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground">Filtri</span>
            <Button variant="ghost" size="sm" className="ml-auto h-7 gap-1 text-xs" onClick={resetFilters}>
              <RotateCcw className="h-3.5 w-3.5" />
              Reset
            </Button>
          </div>

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <Input type="date" value={dataDa} onChange={(e) => setDataDa(e.target.value)} />
            <Input type="date" value={dataA} onChange={(e) => setDataA(e.target.value)} />
            <Select value={flow} onValueChange={(v) => setFlow(v as FlowFilter)}>
              <SelectTrigger>
                <SelectValue placeholder="Flusso" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">Entrate + Uscite</SelectItem>
                <SelectItem value="ENTRATA">Solo entrate</SelectItem>
                <SelectItem value="USCITA">Solo uscite</SelectItem>
              </SelectContent>
            </Select>
            <Select value={action} onValueChange={(v) => setAction(v as ActionFilter)}>
              <SelectTrigger>
                <SelectValue placeholder="Azione" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">Tutte le azioni</SelectItem>
                <SelectItem value="CREATE">CREATE</SelectItem>
                <SelectItem value="UPDATE">UPDATE</SelectItem>
                <SelectItem value="DELETE">DELETE</SelectItem>
                <SelectItem value="RESTORE">RESTORE</SelectItem>
              </SelectContent>
            </Select>
            <Select value={entityType} onValueChange={(v) => setEntityType(v as EntityFilter)}>
              <SelectTrigger className="sm:col-span-2">
                <SelectValue placeholder="Entita&apos;" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">Tutte le entita&apos; cassa</SelectItem>
                <SelectItem value="movement">Movimenti</SelectItem>
                <SelectItem value="recurring_expense">Spese fisse</SelectItem>
                <SelectItem value="rate">Rate</SelectItem>
                <SelectItem value="contract">Contratti</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {data ? `${items.length}/${total} eventi` : "-"}
            </span>
            <Button variant="outline" size="sm" className="h-7 text-xs" onClick={handleRefresh}>
              {isFetching && !isLoadingMore && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
              Aggiorna
            </Button>
          </div>
        </div>

        <ScrollArea className="min-h-0 flex-1 px-4 pb-4">
          <div className="space-y-3 pt-3">
            {isFirstPageLoading && Array.from({ length: 4 }).map((_, idx) => (
              <Skeleton key={idx} className="h-28 w-full rounded-lg" />
            ))}

            {!isFirstPageLoading && items.length === 0 && (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <p className="text-sm font-medium">Nessun evento trovato</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Prova a cambiare periodo o filtri.
                </p>
              </div>
            )}

            {!isFirstPageLoading && items.map((item) => (
              <AuditRow
                key={item.id}
                item={item}
                onNavigateInCash={onNavigateInCash}
              />
            ))}

            {!isFirstPageLoading && hasMore && (
              <Button
                variant="outline"
                className="w-full"
                disabled={isLoadingMore}
                onClick={() => fetchNextPage()}
              >
                {isLoadingMore && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Carica altri
              </Button>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
