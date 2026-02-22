// src/components/agenda/EventSheet.tsx
"use client";

/**
 * Sheet laterale per creare/modificare un evento.
 *
 * Pattern da ContractSheet: apre da destra, contiene il form,
 * si chiude su successo della mutation.
 */

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { EventForm, type EventSubmitPayload } from "./EventForm";
import { useCreateEvent, useUpdateEvent } from "@/hooks/useAgenda";
import type { CalendarEvent } from "./calendar-setup";

interface EventSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  event?: CalendarEvent | null;
  defaultStart?: Date;
  defaultEnd?: Date;
  onDeleteRequest?: () => void;
}

export function EventSheet({
  open,
  onOpenChange,
  event,
  defaultStart,
  defaultEnd,
  onDeleteRequest,
}: EventSheetProps) {
  const isEdit = !!event;
  const createMutation = useCreateEvent();
  const updateMutation = useUpdateEvent();

  const isPending = createMutation.isPending || updateMutation.isPending;

  const handleSubmit = (values: EventSubmitPayload) => {
    if (isEdit) {
      updateMutation.mutate(
        {
          id: event.id,
          data_inizio: values.data_inizio,
          data_fine: values.data_fine,
          titolo: values.titolo,
          note: values.note,
          stato: values.stato,
        },
        { onSuccess: () => onOpenChange(false) }
      );
    } else {
      createMutation.mutate(
        {
          data_inizio: values.data_inizio,
          data_fine: values.data_fine,
          categoria: values.categoria,
          titolo: values.titolo,
          id_cliente: values.id_cliente,
          stato: values.stato,
          note: values.note,
        },
        { onSuccess: () => onOpenChange(false) }
      );
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>
            {isEdit ? "Modifica Evento" : "Nuovo Evento"}
          </SheetTitle>
        </SheetHeader>
        <div className="mt-6">
          <EventForm
            key={event?.id ?? "new"}
            event={event}
            defaultStart={defaultStart}
            defaultEnd={defaultEnd}
            onSubmit={handleSubmit}
            onDelete={isEdit ? onDeleteRequest : undefined}
            isPending={isPending}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
