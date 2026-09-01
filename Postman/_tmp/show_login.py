import io

with io.open(r"_tmp/login_run4.txt", encoding="utf-8", errors="replace") as fh:
    for line in fh:
        if "LOGIN-headers" in line or "LOGIN-body" in line or "Set-Cookie" in line:
            print(line.rstrip("\r\n"))
