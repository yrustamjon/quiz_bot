import { ChevronDown } from "lucide-react";
import * as Dropdown from "@radix-ui/react-dropdown-menu";
import { Link } from "react-router-dom";
import type { User } from "../services/api";
export function AccountMenu({
  user,
  onLogout,
}: {
  user: User;
  onLogout: () => void;
}) {
  return (
    <Dropdown.Root>
      <Dropdown.Trigger className="account-trigger" aria-label="Hisob menyusi">
        <span className="avatar">
          {(user.full_name || user.username)
            .split(" ")
            .slice(0, 2)
            .map((word) => word.slice(0, 1))
            .join("")
            .toUpperCase()}
        </span>
        <span className="account-identity">
          <strong>{user.full_name || user.username}</strong>
          <small>
            {user.role === "SUPER_ADMIN" ? "Administrator" : "O‘qituvchi"}
          </small>
        </span>
        <ChevronDown size={14} className="account-chevron" />
      </Dropdown.Trigger>
      <Dropdown.Portal>
        <Dropdown.Content className="account-menu" sideOffset={10} align="end">
          <Dropdown.Label className="hint">
            {user.full_name || user.username}
          </Dropdown.Label>
          <Dropdown.Separator />
          <Dropdown.Item asChild>
            <Link to="/profile">Profil</Link>
          </Dropdown.Item>
          <Dropdown.Item asChild>
            <Link to="/change-password">Parolni almashtirish</Link>
          </Dropdown.Item>
          <Dropdown.Separator />
          <Dropdown.Item onSelect={onLogout}>Hisobdan chiqish</Dropdown.Item>
        </Dropdown.Content>
      </Dropdown.Portal>
    </Dropdown.Root>
  );
}
