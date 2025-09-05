# backend/agents/python/sender.py
import logging
import requests
import time
from typing import Optional

LOG = logging.getLogger("sender")

def send_event(server_url: str, token: Optional[str], event: dict, verify_tls: bool = False):
    """
    Отправка одного события на backend сервер через HTTP POST.
    """
    url = f"{server_url}/api/events/ingest"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Log request details
    LOG.debug("Sending HTTP POST request:")
    LOG.debug("   URL: %s", url)
    LOG.debug("   Headers: %s", headers)
    LOG.debug("   Event: %s", event)
    
    start_time = time.time()
    
    try:
        resp = requests.post(url, json=event, headers=headers, verify=verify_tls, timeout=5)
        end_time = time.time()
        
        # Log response
        LOG.debug("HTTP response received in %.3f sec:", end_time - start_time)
        LOG.debug("   Status: %d", resp.status_code)
        LOG.debug("   Response: %s", resp.text)
        
        if resp.status_code != 200:
            LOG.warning("Failed to send event: %s %s", resp.status_code, resp.text)
        else:
            LOG.info("Event sent successfully to %s", url)
            LOG.debug("   Event ID: %s", event.get('event_type', 'unknown'))
            
    except requests.exceptions.Timeout:
        LOG.error("Timeout sending event (5 sec)")
    except requests.exceptions.ConnectionError as e:
        LOG.error("Connection error: %s", e)
    except Exception as e:
        LOG.error("Error sending event: %s", e)
        LOG.exception("Full error traceback:")


def send_batch(server_url: str, token: Optional[str], events: list[dict], verify_tls: bool = False):
    """
    Отправка пачки событий.
    """
    url = f"{server_url}/api/events/ingest/batch"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Log request details
    LOG.debug("Sending HTTP POST batch request:")
    LOG.debug("   URL: %s", url)
    LOG.debug("   Headers: %s", headers)
    LOG.debug("   Events count: %d", len(events))
    
    start_time = time.time()
    
    try:
        resp = requests.post(url, json={"events": events}, headers=headers, verify=verify_tls, timeout=10)
        end_time = time.time()
        
        # Log response
        LOG.debug("HTTP batch response received in %.3f sec:", end_time - start_time)
        LOG.debug("   Status: %d", resp.status_code)
        LOG.debug("   Response: %s", resp.text)
        
        if resp.status_code != 200:
            LOG.warning("Failed to send batch: %s %s", resp.status_code, resp.text)
        else:
            LOG.info("Batch sent successfully (%d events) to %s", len(events), url)
            
    except requests.exceptions.Timeout:
        LOG.error("Timeout sending batch (10 sec)")
    except requests.exceptions.ConnectionError as e:
        LOG.error("Connection error: %s", e)
    except Exception as e:
        LOG.error("Error sending batch: %s", e)
        LOG.exception("Full error traceback:")
