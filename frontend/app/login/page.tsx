import LoginForm from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-4 py-12">
      <div className="mb-8 text-center">
        <div className="mb-2 text-3xl font-semibold text-slate-100">🏥 MediBot</div>
        <div className="text-sm text-slate-400">
          Role-aware RAG assistant for MediAssist Health Network
        </div>
      </div>
      <div className="w-full rounded-xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl">
        <LoginForm />
      </div>
      <p className="mt-6 text-xs text-slate-500">
        Plaintext demo passwords are intentional — see README.
      </p>
    </main>
  );
}
