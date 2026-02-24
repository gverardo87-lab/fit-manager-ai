// src/components/exercises/ExercisesTable.tsx
"use client";

/**
 * Tabella esercizi con ricerca client-side, badge colorati, dropdown azioni.
 * Gli esercizi builtin non hanno azioni di modifica/eliminazione.
 */

import { useState, useMemo } from "react";
import { Search, MoreHorizontal, Pencil, Trash2, Dumbbell, Lock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import {
  CATEGORY_LABELS,
  CATEGORY_COLORS,
  DIFFICULTY_LABELS,
  DIFFICULTY_COLORS,
  EQUIPMENT_LABELS,
  MUSCLE_LABELS,
} from "./exercise-constants";
import type { Exercise } from "@/types/api";

interface ExercisesTableProps {
  exercises: Exercise[];
  onEdit: (exercise: Exercise) => void;
  onDelete: (exercise: Exercise) => void;
  onNewExercise?: () => void;
}

export function ExercisesTable({
  exercises,
  onEdit,
  onDelete,
  onNewExercise,
}: ExercisesTableProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return exercises;
    const q = search.toLowerCase();
    return exercises.filter(
      (e) =>
        e.nome.toLowerCase().includes(q) ||
        e.nome_en?.toLowerCase().includes(q) ||
        e.muscoli_primari.some((m) => (MUSCLE_LABELS[m] ?? m).toLowerCase().includes(q))
    );
  }, [exercises, search]);

  return (
    <div className="space-y-3">
      {/* ── Search ── */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Cerca esercizio..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* ── Empty State ── */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-12">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Dumbbell className="h-6 w-6 text-muted-foreground/50" />
          </div>
          <div className="text-center">
            <p className="font-medium text-muted-foreground">
              {search ? "Nessun risultato" : "Nessun esercizio"}
            </p>
            {!search && onNewExercise && (
              <Button variant="link" size="sm" onClick={onNewExercise} className="mt-1">
                Crea il primo esercizio
              </Button>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border bg-white dark:bg-zinc-900">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead className="hidden sm:table-cell">Categoria</TableHead>
                <TableHead className="hidden md:table-cell">Muscoli</TableHead>
                <TableHead className="hidden lg:table-cell">Attrezzatura</TableHead>
                <TableHead className="hidden sm:table-cell">Difficolta&apos;</TableHead>
                <TableHead className="w-[50px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((exercise) => (
                <TableRow key={exercise.id}>
                  {/* Nome */}
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{exercise.nome}</span>
                      {exercise.is_builtin && (
                        <Tooltip>
                          <TooltipTrigger>
                            <Lock className="h-3 w-3 text-muted-foreground/50" />
                          </TooltipTrigger>
                          <TooltipContent>Esercizio builtin</TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                    {exercise.nome_en && exercise.nome_en !== exercise.nome && (
                      <p className="text-xs text-muted-foreground">{exercise.nome_en}</p>
                    )}
                  </TableCell>

                  {/* Categoria */}
                  <TableCell className="hidden sm:table-cell">
                    <Badge
                      variant="secondary"
                      className={CATEGORY_COLORS[exercise.categoria] ?? ""}
                    >
                      {CATEGORY_LABELS[exercise.categoria] ?? exercise.categoria}
                    </Badge>
                  </TableCell>

                  {/* Muscoli */}
                  <TableCell className="hidden md:table-cell">
                    <div className="flex flex-wrap gap-1">
                      {exercise.muscoli_primari.slice(0, 3).map((m) => (
                        <Badge key={m} variant="outline" className="text-xs">
                          {MUSCLE_LABELS[m] ?? m}
                        </Badge>
                      ))}
                      {exercise.muscoli_primari.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{exercise.muscoli_primari.length - 3}
                        </Badge>
                      )}
                    </div>
                  </TableCell>

                  {/* Attrezzatura */}
                  <TableCell className="hidden lg:table-cell">
                    {EQUIPMENT_LABELS[exercise.attrezzatura] ?? exercise.attrezzatura}
                  </TableCell>

                  {/* Difficolta' */}
                  <TableCell className="hidden sm:table-cell">
                    <Badge
                      variant="secondary"
                      className={DIFFICULTY_COLORS[exercise.difficolta] ?? ""}
                    >
                      {DIFFICULTY_LABELS[exercise.difficolta] ?? exercise.difficolta}
                    </Badge>
                  </TableCell>

                  {/* Azioni */}
                  <TableCell>
                    {!exercise.is_builtin && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onEdit(exercise)}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Modifica
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => onDelete(exercise)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Elimina
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
