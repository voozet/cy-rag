"use client";
import Link from "next/link";
import Image from "next/image";
import {usePathname} from "next/navigation";

export function Sidebar({mobileOpen = false}: { mobileOpen?: boolean }) {
    const pathname = usePathname();
    const item = (href: string, label: string) =>
        <Link href={href} className={`navItem${pathname === href ? " active" : ""}`}>{label}</Link>;

    return <aside className={`sidebar${mobileOpen ? " open" : ""}`}>
        <div className="brand">
            <div className="brandMark">
                <Image src="/shield-mark.svg" alt="" width={20} height={20}/>
            </div>
            <div>
                <div className="brandTitle">CyberRAG</div>
                <div className="brandSub">UNB · Canadian Institute for Cybersecurity</div>
            </div>
        </div>
        <nav className="nav">
            {item("/", "Assistant")}
            {item("/admin", "Knowledge Base")}
            {item("/evaluation", "Evaluation")}
            {item("/doc", "Documentation")}
        </nav>
        <div className="sideBottom">
            <div className="online"><span className="dot"/>System online</div>
            <div style={{marginTop: 7}}>Evidence-first response pipeline</div>
        </div>
    </aside>
}
