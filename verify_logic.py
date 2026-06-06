import psutil

print("--- DIAGNOSTIC START ---")

# 1. Get All Interfaces
interfaces = psutil.net_if_addrs()
print(f"Found {len(interfaces)} total interfaces.")

# 2. Simulate Auto-Detect Logic
selected_interface = None
wifi_candidates = []

print("\n--- Scanning for Wi-Fi ---")
for iface in interfaces.keys():
    is_wifi = "wi-fi" in iface.lower() or "wireless" in iface.lower()
    print(f"Interface: '{iface}' | Is Wi-Fi? {is_wifi}")
    if is_wifi:
        wifi_candidates.append(iface)
        if selected_interface is None:
            selected_interface = iface # Pick first one

print(f"\n[Logic Check] Auto-Selected: {selected_interface}")
print(f"[Logic Check] All Wi-Fi Options: {wifi_candidates}")

# 3. Verify Data Access
print("\n--- Testing Data Reading ---")
if selected_interface:
    try:
        stats = psutil.net_io_counters(pernic=True)
        if selected_interface in stats:
            data = stats[selected_interface]
            print(f"SUCCESS: Could read stats for '{selected_interface}'")
            print(f"  -> Upload: {data.bytes_sent} bytes")
            print(f"  -> Download: {data.bytes_recv} bytes")
        else:
            print(f"CRITICAL ERROR: Interface '{selected_interface}' found in addrs but NOT in counters!")
            print(f"Available Counter Keys: {list(stats.keys())}")
    except Exception as e:
        print(f"ERROR reading stats: {e}")
else:
    print("WARNING: No Wi-Fi found to test.")

print("\n--- DIAGNOSTIC END ---")
