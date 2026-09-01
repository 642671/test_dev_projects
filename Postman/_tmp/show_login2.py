import io

with io.open(r"_tmp/login_run4.txt", encoding="utf-8", errors="replace") as fh:
    for line in fh:
        if "LOGIN-headers" in line:
            print("HEADERS_LEN", len(line))
            print("has_TMSESSNAME", "TMSESSNAME" in line)
            print("has_userName", "userName" in line)
            print("has_tos_current_username", "tos_current_username" in line)
            # 抽 set-cookie 值
            import re
            m = re.search(r'"set-cookie":"([^"]*)"', line)
            print("SETCOOKIE=", m.group(1) if m else "NONE")
            break
