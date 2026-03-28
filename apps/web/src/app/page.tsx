export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold tracking-tight">
        OpsMesh
      </h1>
      <p className="mt-4 text-lg text-gray-600">
        AI-powered incident intelligence platform
      </p>
      <div className="mt-8 flex gap-4">
        <span className="rounded-full bg-green-100 px-3 py-1 text-sm text-green-800">
          System Healthy
        </span>
      </div>
    </main>
  );
}
