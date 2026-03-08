// src/app/(dashboard)/clienti/myportal/page.tsx
// Redirect → /monitoraggio (tab salute)
import { redirect } from "next/navigation";

export default function MyPortalRedirect() {
  redirect("/monitoraggio");
}
