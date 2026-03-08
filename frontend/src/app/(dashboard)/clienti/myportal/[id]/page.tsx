// src/app/(dashboard)/clienti/myportal/[id]/page.tsx
// Redirect → /monitoraggio/[id]
import { redirect } from "next/navigation";

export default async function MyPortalDetailRedirect({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/monitoraggio/${id}`);
}
