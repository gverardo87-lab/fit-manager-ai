import { cn } from "@/lib/utils"

/**
 * Skeleton — shimmer loading placeholder
 *
 * Usa un sweep luminoso (::after) invece del pulse opacity.
 * L'effetto "luce che scorre" è più premium e comunica
 * attivamente che il contenuto sta arrivando.
 *
 * Compatibile dark mode: il layer bianco/40 è visibile
 * sia su sfondi chiari che scuri.
 */
function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      className={cn(
        // Base: stessa forma dell'elemento reale
        "relative overflow-hidden rounded-md bg-muted",
        // Shimmer: layer bianco che scorre da sinistra a destra
        "after:absolute after:inset-0 after:translate-x-[-100%]",
        "after:bg-gradient-to-r after:from-transparent after:via-white/40 after:to-transparent",
        "after:animate-[shimmer_1.8s_ease-in-out_infinite]",
        className
      )}
      {...props}
    />
  )
}

export { Skeleton }
