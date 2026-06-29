import { Routes, Route, Navigate } from "react-router-dom"
import { ProtectedRoute } from "./ProtectedRoute"
import { LoginPage } from "@/features/auth/LoginPage"
import { RegisterPage } from "@/features/auth/RegisterPage"
import { DogProfilePage } from "@/features/onboarding/DogProfilePage"
import { QuizPage } from "@/features/onboarding/QuizPage"
import { DashboardPage } from "@/features/dashboard/DashboardPage"
import { SessionPage } from "@/features/session/SessionPage"

export function AppRouter() {
  return (
    <Routes>
      {/* Públicas */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Privadas */}
      <Route element={<ProtectedRoute />}>
        <Route path="/onboarding/dog" element={<DogProfilePage />} />
        <Route path="/onboarding/quiz" element={<QuizPage />} />
        <Route path="/" element={<DashboardPage />} />
        <Route path="/sesion" element={<SessionPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
