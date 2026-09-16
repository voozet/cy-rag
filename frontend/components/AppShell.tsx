"use client";
import {useEffect, useState} from "react";
import {usePathname} from "next/navigation";
import {Menu, X} from "lucide-react";
import {Sidebar} from "./Sidebar";

export function AppShell({children}: { children: React.ReactNode }) {
    const [open, setOpen] = useState(false);
    const pathname = usePathname();

    // Close the drawer automatically on navigation (e.g. tapping a sidebar link)
    useEffect(() => {
        setOpen(false);
    }, [pathname]);

    useEffect(() => {
        document.body.style.overflow = open ? "hidden" : "";
        return () => {
            document.body.style.overflow = "";
        };
    }, [open]);

    return <div className="app">
        <button className="menuToggle" aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open}
                onClick={() => setOpen(!open)}>
            {open ? <X size={18}/> : <Menu size={18}/>}
        </button>
        <div className={`sidebarBackdrop${open ? " open" : ""}`} onClick={() => setOpen(false)}/>
        <Sidebar mobileOpen={open}/>
        <main className="main">{children}</main>
    </div>;
}
