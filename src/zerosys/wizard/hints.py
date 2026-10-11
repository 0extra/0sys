from __future__ import annotations

HINTS: dict[str, str] = {
    "hostname": (
        "The name your server uses to identify itself. "
        "Something short and simple like 'web-01' or 'my-vps'."
    ),
    "timezone": (
        "Used in logs and scheduled tasks so timestamps make sense. "
        "Pick 'UTC' unless you have a reason."
    ),
    "locale": (
        "Language and character set for the system. en_US.UTF-8 is a safe default everywhere."
    ),
    "role": (
        "A quick preset that fills in common choices. "
        "You can still tweak everything later in the review step."
    ),
    "ssh_key": (
        "A small file on your laptop that proves who you are. "
        "Safer than a password because it cannot be guessed."
    ),
    "admin_user": (
        "A personal account with sudo access, so you do not need to log in as root. "
        "Recommended on every server."
    ),
    "sudo": (
        "Permission to run commands as administrator. "
        "Needed to install packages and change system files."
    ),
    "firewall": (
        "A program that decides which doors on your server are open. "
        "Port 22 is SSH. If you close it, you will lock yourself out."
    ),
    "firewall_default": (
        "'deny' closes everything by default and only opens what you allow. "
        "'allow' opens everything. 'deny' is safer."
    ),
    "ssh_hardening": (
        "Turns off password login. Only SSH keys will work. "
        "Do this only after your SSH key is installed and working."
    ),
    "fail2ban": (
        "Watches logs and temporarily blocks IPs that try to break in. "
        "Cheap and effective on any public server."
    ),
    "nginx": (
        "A web server. Serves websites and handles HTTPS traffic. "
        "Install it if you plan to host anything on port 80 or 443."
    ),
    "docker": (
        "Runs applications in isolated boxes called containers. "
        "Great for services you do not want to install system-wide."
    ),
    "package": (
        "A program from your system's app store (apt on Ubuntu, pacman on Arch, dnf on Fedora)."
    ),
    "extra_packages": (
        "Anything else you want installed right now. You can add more later by editing the config."
    ),
    "review": (
        "Look at what 0sys will do. If something is off, answer 'no' and nothing gets written."
    ),
}


def hint(key: str) -> str:
    return HINTS.get(key, "")
