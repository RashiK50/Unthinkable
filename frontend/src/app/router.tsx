import { Navigate, createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/app/AppLayout";
import { AuthPage } from "@/features/auth/AuthPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { MeetingDetailPage } from "@/features/meetings/MeetingDetailPage";
import { MeetingsPage } from "@/features/meetings/MeetingsPage";

export const router = createBrowserRouter([
  { path: "/login", element: <AuthPage mode="login" /> },
  { path: "/signup", element: <AuthPage mode="signup" /> },
  {
    element: <AppLayout />,
    children: [
      { path: "/dashboard", element: <DashboardPage /> },
      { path: "/meetings", element: <MeetingsPage /> },
      { path: "/meetings/:meetingId", element: <MeetingDetailPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> },
]);
