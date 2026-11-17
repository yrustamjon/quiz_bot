import { Moon, Sun } from "lucide-react";
import { useState } from "react";
export function ThemeToggle() {
  const [dark, setDark] = useState(
    document.documentElement.classList.contains("dark"),
  );
  return (
    <button
      className="icon"
      aria-label={dark ? "Yorug‘ mavzu" : "Qorong‘i mavzu"}
      onClick={() => {
        document.documentElement.classList.toggle("dark", !dark);
        localStorage.theme = dark ? "light" : "dark";
        setDark(!dark);
      }}
    >
      {dark ? <Sun size={19} /> : <Moon size={19} />}
    </button>
  );
}
