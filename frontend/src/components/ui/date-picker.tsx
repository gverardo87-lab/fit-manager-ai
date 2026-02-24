// src/components/ui/date-picker.tsx
"use client";

/**
 * DatePicker — Popover + Calendar di shadcn, formattato in italiano.
 *
 * Props:
 * - value: Date | undefined
 * - onChange: (date: Date | undefined) => void
 * - placeholder: testo quando nessuna data selezionata
 * - disabled: disabilita il picker
 */

import { format } from "date-fns";
import { it } from "date-fns/locale";
import { CalendarIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface DatePickerProps {
  value?: Date;
  onChange: (date: Date | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  maxDate?: Date;
}

export function DatePicker({
  value,
  onChange,
  placeholder = "Seleziona data...",
  disabled = false,
  maxDate,
}: DatePickerProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          disabled={disabled}
          className={cn(
            "w-full justify-start text-left font-normal",
            !value && "text-muted-foreground"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {value ? format(value, "dd MMMM yyyy", { locale: it }) : placeholder}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={value}
          onSelect={onChange}
          locale={it}
          initialFocus
          toDate={maxDate}
        />
      </PopoverContent>
    </Popover>
  );
}
