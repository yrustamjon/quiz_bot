import { UnsavedChangesProvider } from "./components/useUnsavedChanges";
import { ConfirmationProvider } from "./components/ConfirmationProvider";
import "./services/validation";
import { Notifications } from "./components/Notifications";
import React, { Suspense, lazy } from "react";
import { createRoot } from "react-dom/client";
import {
  createBrowserRouter,
  createRoutesFromElements,
  RouterProvider,
  Outlet,
  Route,
  Navigate,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./services/auth";
import { Loading } from "./components/states";
import "./style.css";
const Auth = lazy(() => import("./pages/Auth"));
const Shell = lazy(() => import("./layouts/Shell"));
const Quizzes = lazy(() => import("./pages/Quizzes"));
const Detail = lazy(() => import("./pages/QuizDetail"));
const Directory = lazy(() => import("./pages/Directory"));
const Profile = lazy(() => import("./pages/Profile"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Results = lazy(() => import("./pages/Results"));
const StudentDetail = lazy(() => import("./pages/StudentDetail"));
const Groups = lazy(() => import("./pages/Groups"));
const Teachers = lazy(() => import("./pages/Teachers"));
const query = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
});
const router = createBrowserRouter(
  createRoutesFromElements(
    <Route
      element={
        <ConfirmationProvider>
          <UnsavedChangesProvider>
            <Suspense fallback={<Loading />}>
              <Outlet />
            </Suspense>
          </UnsavedChangesProvider>
        </ConfirmationProvider>
      }
    >
      <Route path="login" element={<Auth />} />
      <Route path="change-password" element={<Auth change />} />
      <Route element={<Shell />}>
        <Route index element={<Dashboard />} />
        <Route path="quizzes" element={<Quizzes />} />
        <Route path="quizzes/:id" element={<Detail />} />
        {(["students", "questions"] as const).map((kind) => (
          <Route key={kind} path={kind} element={<Directory kind={kind} />} />
        ))}
        <Route path="students/:id" element={<StudentDetail />} />
        <Route path="results" element={<Results />} />
        <Route path="rankings" element={<Results ranking />} />
        <Route path="reports" element={<Results report />} />
        <Route path="groups" element={<Groups />} />
        <Route path="settings" element={<Profile />} />
        <Route path="teachers" element={<Teachers />} />
        <Route path="profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" />} />
    </Route>,
  ),
);
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={query}>
      <Notifications />
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
