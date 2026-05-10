import { createBrowserRouter } from "react-router-dom";
import App from "../App";
import { DashboardPage } from "../pages/dashboard-page";
import { HomePage } from "../pages/home-page";
import { LoginPage } from "../pages/login-page";
import { NotFoundPage } from "../pages/not-found-page";
import { PlanDetailPage } from "../pages/plan-detail-page";
import { PlansPage } from "../pages/plans-page";
import { QaPage } from "../pages/qa-page";
import { RecommendationPage } from "../pages/recommendation-page";
import { RegisterPage } from "../pages/register-page";
import { ReportsPage } from "../pages/reports-page";
import { SchoolsPage } from "../pages/schools-page";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      {
        path: "dashboard",
        element: <DashboardPage />,
      },
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: "login",
        element: <LoginPage />,
      },
      {
        path: "register",
        element: <RegisterPage />,
      },
      {
        path: "plans",
        element: <PlansPage />,
      },
      {
        path: "plans/:planId",
        element: <PlanDetailPage />,
      },
      {
        path: "recommendation",
        element: <RecommendationPage />,
      },
      {
        path: "schools",
        element: <SchoolsPage />,
      },
      {
        path: "qa",
        element: <QaPage />,
      },
      {
        path: "reports",
        element: <ReportsPage />,
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
