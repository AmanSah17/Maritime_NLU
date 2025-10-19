import streamlit as st
import requests
from streamlit_folium import st_folium
import folium
import os

st.set_page_config(page_title="NLU Chatbot", layout="wide")

# Robust backend base URL lookup: try Streamlit secrets, fall back to env var, then default
try:
    backend_base = st.secrets.get("BACKEND_BASE", None)
except Exception:
    backend_base = None
if not backend_base:
    backend_base = os.environ.get("BACKEND_BASE", "http://localhost:8000")

st.title("NLU Chatbot — spaCy backend")

col1, col2 = st.columns([2, 1])

with col1:
    user_text = st.text_area("Ask about a vessel (e.g. 'Where was ABIGAIL at 6:25 PM on Jan 5, 2020?')", height=120)
    if st.button("Send"):
        if not user_text.strip():
            st.warning("Type a question first")
        else:
            try:
                r = requests.post(f"{backend_base}/query", json={"text": user_text}, timeout=25)
                data = r.json()
                parsed = data.get("parsed", {})
                st.subheader("Parsed NLU")
                st.json(parsed)

                # Helper to submit background job and poll for result
                def _submit_and_poll(params, timeout_seconds=60, poll_interval=1.5):
                    """Submit /admin/submit_query_job with params and poll /admin/job_status/{job_id}.
                    Returns the job result dict or None on timeout/failure."""
                    job_id = None
                    try:
                        submit = requests.post(f"{backend_base}/admin/submit_query_job", params=params, timeout=10)
                        job = submit.json()
                        job_id = job.get("job_id")
                    except Exception as e:
                        st.error(f"Failed to submit background job: {e}")
                        return None

                    poll_url = f"{backend_base}/admin/job_status/{job_id}"
                    import time
                    elapsed = 0.0
                    with st.spinner("Query running on server, polling for result..."):
                        while elapsed < timeout_seconds:
                            try:
                                rcheck = requests.get(poll_url, timeout=10)
                                status = rcheck.json()
                            except Exception as e:
                                st.warning(f"Polling error: {e}")
                                status = {"status": "PENDING"}

                            if status.get("status") == "DONE":
                                return status.get("result")
                            if status.get("status") == "FAILED":
                                st.error(f"Background job failed: {status.get('error')}")
                                return status.get("result")

                            time.sleep(poll_interval)
                            elapsed += poll_interval

                    # timed out
                    st.info("Background job timed out waiting for result")
                    return None

                # Allow quick run of DB query using parsed JSON
                if st.button("Query DB for parsed NLU"):
                    # Build params from parsed JSON
                    identifiers = parsed.get("identifiers", {}) or {}
                    vessel_name = parsed.get("vessel_name")
                    mmsi = identifiers.get("mmsi")
                    params = {}
                    if mmsi:
                        params["mmsi"] = mmsi
                    elif vessel_name:
                        params["vessel"] = vessel_name

                    # Prefer explicit end_dt from parsed NLU if present
                    if parsed.get("end_dt"):
                        params["end_dt"] = parsed.get("end_dt")
                    elif parsed.get("datetime"):
                        params["end_dt"] = parsed.get("datetime")

                    describe = None
                    if params:
                        describe = _submit_and_poll(params, timeout_seconds=60)

                    # Render describe result in right column
                    with col2:
                        if describe is None:
                            st.info("No result returned from the backend (timeout or error).")
                        else:
                            # Prefer human-friendly message
                            if isinstance(describe, dict) and describe.get("message"):
                                st.markdown(f"**Bot:** {describe.get('message')}")

                            if isinstance(describe, dict) and describe.get("track"):
                                import pandas as pd
                                try:
                                    df = pd.DataFrame(describe.get("track"))
                                    st.dataframe(df)
                                except Exception:
                                    st.json(describe)
                            else:
                                st.json(describe)

                # Use parsed JSON to build a targeted DB query (NLU-first)
                identifiers = parsed.get("identifiers", {}) or {}
                vessel_name = parsed.get("vessel_name")
                mmsi = identifiers.get("mmsi")

                # Compute end_dt from parsed datetime or time_horizon
                end_dt = None
                parsed_dt = parsed.get("datetime")
                time_horizon = parsed.get("time_horizon")
                if parsed_dt:
                    # if returned as HH:MM:SS treat as time-of-day today
                    if len(parsed_dt) <= 8 and ":" in parsed_dt:
                        # attach today's date
                        from datetime import datetime
                        today = datetime.utcnow().strftime("%Y-%m-%d")
                        end_dt = f"{today} {parsed_dt}"
                    else:
                        end_dt = parsed_dt
                elif time_horizon:
                    # simple heuristic: if 'last X minutes' treat end_dt as now
                    import re
                    m = re.search(r"(\d+)\s*(minutes|minute)", time_horizon)
                    if m:
                        minutes = int(m.group(1))
                        from datetime import datetime, timedelta
                        end_dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                params = {}
                if mmsi:
                    params["mmsi"] = mmsi
                elif vessel_name:
                    params["vessel"] = vessel_name

                if params:
                    if end_dt:
                        params["end_dt"] = end_dt
                    # Submit a background job to avoid timeouts for large DB queries
                    try:
                        submit = requests.post(f"{backend_base}/admin/submit_query_job", params=params, timeout=10)
                        job = submit.json()
                        job_id = job.get("job_id")
                    except Exception as e:
                        st.error(f"Failed to submit background job: {e}")
                        job_id = None

                    describe = None
                    if job_id:
                        # Poll for job completion with a spinner and timeout
                        import time
                        poll_url = f"{backend_base}/admin/job_status/{job_id}"
                        with st.spinner("Query running on server, polling for result..."):
                            timeout_seconds = 60
                            interval = 1.5
                            elapsed = 0.0
                            while elapsed < timeout_seconds:
                                try:
                                    rcheck = requests.get(poll_url, timeout=10)
                                    status = rcheck.json()
                                except Exception as e:
                                    st.warning(f"Polling error: {e}")
                                    status = {"status": "PENDING"}

                                if status.get("status") == "DONE":
                                    describe = status.get("result")
                                    break
                                if status.get("status") == "FAILED":
                                    st.error(f"Background job failed: {status.get('error')}")
                                    describe = status.get("result")
                                    break
                                time.sleep(interval)
                                elapsed += interval

                    if describe is None:
                        st.info("No result yet. Try increasing the polling timeout or check server logs.")
                    else:
                        st.subheader("Describe Vessel / Track")
                        # Prefer human-friendly message if present
                        if isinstance(describe, dict) and describe.get("message"):
                            st.markdown(f"**Bot:** {describe.get('message')}")

                        # show tabular track results if present
                        if isinstance(describe, dict) and describe.get("track"):
                            import pandas as pd
                            try:
                                df = pd.DataFrame(describe.get("track"))
                                st.dataframe(df)
                            except Exception:
                                st.json(describe)
                        else:
                            # fallback: show raw describe JSON if no track is present
                            st.json(describe)

                    # Plot location if available
                    last_pos = None
                    if isinstance(describe, dict):
                        # describe may include 'last_seen' with lat/lon or a small track
                        if "last_seen" in describe:
                            ls = describe.get("last_seen")
                            if ls and ls.get("lat") and ls.get("lon"):
                                last_pos = (ls.get("lat"), ls.get("lon"))
                        if not last_pos and describe.get("sample_track"):
                            st.write("Sample track available; plotting last point")
                            track = describe.get("sample_track")
                            if isinstance(track, list) and track:
                                rec = track[-1]
                                last_pos = (rec.get("LAT"), rec.get("LON"))

                    if last_pos:
                        m = folium.Map(location=last_pos, zoom_start=8)
                        folium.Marker(location=last_pos, tooltip=f"{vessel_name or ''} {mmsi or ''}",
                                      icon=folium.Icon(color="blue", icon="ship", prefix='fa')).add_to(m)
                        st_folium(m, width=700, height=450)
                    else:
                        st.info("No position available to plot for this vessel/result")
                else:
                    st.info("No vessel name or MMSI parsed from the query; try specifying the vessel name or MMSI.")
            except Exception as e:
                st.error(f"Request failed: {e}")

with col2:
    st.markdown("### Tips")
    st.markdown("- Use exact vessel names or MMSI when possible for best results.")
    st.markdown("- Date/time can be partial (e.g., '6:25 PM' or 'Jan 5').")
    st.markdown("- This page uses the server-side spaCy NLU only — no client transformers are used.")
