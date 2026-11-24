import { StrictMode, lazy, Suspense, useEffect } from "react"
import { createRoot } from "react-dom/client"
import { HashRouter, Navigate, Route, Routes, useLocation } from "react-router-dom"
import { SiteLayout } from "@/components/site/SiteLayout"
import { Home } from "@/pages/Home"
import "./styles.css"

// Heavy pages load on demand so the home page stays fast.
const World = lazy(() => import("@/pages/World"))
const SmokeCast = lazy(() => import("@/pages/SmokeCast"))
const AirPlan = lazy(() => import("@/pages/AirPlan"))
const About = lazy(() => import("@/pages/About"))

const TITLES: Record<string, string> = {
  "/smokecast": "SmokeCast",
  "/world": "Smoke World",
  "/airplan": "AirPlan",
  "/about": "Data and methods",
}

function DocumentTitle() {
  const { pathname } = useLocation()
  useEffect(() => {
    const title = TITLES[pathname]
    document.title = title ? `${title} | Serein` : "Serein | Wildfire Smoke Forecasts"
  }, [pathname])
  return null
}

function Loading() {
  return <div role="status" className="grid min-h-[60vh] place-items-center text-muted-foreground">Loading page…</div>
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <HashRouter>
      <DocumentTitle />
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/world" element={<World />} />
          <Route element={<SiteLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/smokecast" element={<SmokeCast />} />
            <Route path="/airplan" element={<AirPlan />} />
            <Route path="/about" element={<About />} />
            <Route path="/results" element={<Navigate to="/smokecast" replace />} />
            <Route path="/replay" element={<Navigate to="/smokecast" replace />} />
            <Route path="/plan" element={<Navigate to="/airplan" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </HashRouter>
  </StrictMode>,
)
