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
      <Dropdown.Trigger className="avatar icon" aria-label="Hisob menyusi">
        {(user.full_name || user.username).slice(0, 1).toUpperCase()}
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
