import { Routes, Route, Navigate } from "react-router-dom"
import { ProtectedRoute } from "./ProtectedRoute"
import { LoginPage } from "@/features/auth/LoginPage"
import { RegisterPage } from "@/features/auth/RegisterPage"
import { DogProfilePage } from "@/features/onboarding/DogProfilePage"
import { QuizPage } from "@/features/onboarding/QuizPage"
import { DashboardPage } from "@/features/dashboard/DashboardPage"
import { SessionPage } from "@/features/session/SessionPage"
import { PlanPage } from "@/features/plan/PlanPage"
import { ProfilePage } from "@/features/profile/ProfilePage"
import { EditProfilePage } from "@/features/profile/EditProfilePage"
import { DogsPage } from "@/features/dogs/DogsPage"
import { ExerciseTechniquePage } from "@/features/technique/ExerciseTechniquePage"

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
        <Route path="/plan" element={<PlanPage />} />
        <Route path="/sesion" element={<SessionPage />} />
        <Route path="/perfil" element={<ProfilePage />} />
        <Route path="/perfil/editar" element={<EditProfilePage />} />
        <Route path="/perros" element={<DogsPage />} />
        <Route path="/ejercicio/:exerciseId" element={<ExerciseTechniquePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
