// src/app/(dashboard)/allenamenti/mytrainer/page.tsx
// Redirect → /monitoraggio (tab programmi)
import { redirect } from "next/navigation";

export default function MyTrainerRedirect() {
  redirect("/monitoraggio");
}
