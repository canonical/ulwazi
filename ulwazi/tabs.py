# This file is part of Ulwazi.
#
# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3, as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranties of MERCHANTABILITY, SATISFACTORY
# QUALITY, or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""Styles and structures sphinx-tabs in accordance with Vanilla."""

from contextlib import suppress

from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList


def convert_tabs(body_html: str) -> str:  # noqa: PLR0912, PLR0915
    """Convert sphinx-tabs markup to vanilla theme classes and structure."""
    if not body_html:
        return body_html

    soup = BeautifulSoup(body_html, "html.parser")

    # 1. Update sphinx-tabs docutils container to include p-tabs
    for tab_container in soup.find_all("div", class_="sphinx-tabs"):
        classes = tab_container.get("class")
        class_list = list(classes) if classes else []
        if "p-tabs" not in class_list:
            class_list.append("p-tabs")
        tab_container["class"] = " ".join(class_list)

        # Find the tablist
        tablist = tab_container.find("div", attrs={"role": "tablist"})
        if tablist:
            # Get all tab buttons
            tab_buttons = tablist.find_all("button", class_="p-tabs__link")
            # Remove all buttons from tablist
            for btn in tab_buttons:
                btn.extract()
            # Wrap each button in a div.p-tabs__item and re-add
            for btn in tab_buttons:
                item_div = soup.new_tag("div", attrs={"class": "p-tabs__item"})
                item_div.append(btn)
                tablist.append(item_div)

    # 2. Update tablist div to p-tabs__list
    for tablist in soup.find_all("div", attrs={"role": "tablist"}):
        tablist_classes = tablist.get("class")
        class_list = list(tablist_classes) if tablist_classes else []
        if "closeable" in class_list:
            class_list.remove("closeable")
        if "p-tabs__list" not in class_list:
            class_list.append("p-tabs__list")
        tablist["class"] = " ".join(class_list)

    # 3. Update tab buttons to p-tabs__link
    for tab_button in soup.find_all("button"):
        btn_classes = tab_button.get("class")
        class_list = list(btn_classes) if btn_classes else []
        if "sphinx-tabs-tab" in class_list:
            class_list.remove("sphinx-tabs-tab")
        if "p-tabs__link" not in class_list:
            class_list.append("p-tabs__link")
        tab_button["class"] = " ".join(class_list)
        tab_button["role"] = "tab"

        # Add sync attributes for sphinx-tabs
        tab_text = tab_button.get_text(strip=True)
        sync_value = str(tab_text).strip().lower().replace(" ", "-") if tab_text else ""
        tab_button["data-sync-value"] = sync_value
        # If a group or sync id is present, add as data-sync-id
        sync_id = tab_button.get("data-sync-id")
        if not sync_id:
            # Try to infer from parent or attributes
            parent = tab_button.find_parent("div", class_="sphinx-tabs")
            found = False
            if parent:
                # Sphinx-tabs may use data-group or data-sync attributes
                for attr in ["data-group", "data-sync"]:
                    val = parent.get(attr)
                    if val:
                        tab_button["data-sync-id"] = val
                        found = True
                        break
            if not found:
                # Always set a default sync-id for sphinx-tabs
                tab_button["data-sync-id"] = "tab"

    # 4. Update sphinx-tabs-panel to p-tabs__item (for panels)
    panel: Tag | None
    for panel in soup.find_all(class_="sphinx-tabs-panel"):
        panel_classes = panel.get("class")
        class_list = list(panel_classes) if panel_classes else []
        if "sphinx-tabs-panel" in class_list:
            class_list.remove("sphinx-tabs-panel")
        if "p-tabs__item" not in class_list:
            class_list.append("p-tabs__item")
        panel["class"] = " ".join(class_list)

    # 5+. Convert sphinx-design `sd-tab-set` blocks into Vanilla tabs structure
    for sd_index, sd_container in enumerate(soup.find_all("div", class_="sd-tab-set")):
        # ensure container is marked as p-tabs
        existing = sd_container.get("class")
        existing_list = list(existing) if existing else []
        if "p-tabs" not in existing_list:
            existing_list.append("p-tabs")
        sd_container["class"] = " ".join(existing_list)

        # collect radios, labels and panels (in the order they appear)
        inputs = sd_container.find_all("input", type="radio")
        labels = sd_container.find_all("label", class_="sd-tab-label")
        panels = sd_container.find_all("div", class_="sd-tab-content")

        # find or create the tablist (insert before first panel)
        tablist = sd_container.find("div", attrs={"role": "tablist"})
        if not tablist:
            tablist = soup.new_tag("div")
            tablist["role"] = "tablist"
            tablist["class"] = "p-tabs__list"
            # insert tablist as first child of sd_container
            first_child = next(
                (c for c in sd_container.contents if isinstance(c, Tag)), None
            )
            if first_child:
                first_child.insert_before(tablist)
            else:
                sd_container.append(tablist)
        else:
            # ensure correct class
            tl_classes = tablist.get("class")
            tl_list = list(tl_classes) if tl_classes else []
            if "p-tabs__list" not in tl_list:
                tl_list.append("p-tabs__list")
            tablist["class"] = " ".join(tl_list)

        # Determine number of tabs to build (prefer inputs+labels alignment, then panels)
        n = max(len(inputs), len(labels), len(panels))

        # Build mapping lists for ids and text
        for idx in range(n):
            # find associated input, label and panel by index (fallbacks allowed)
            inp = inputs[idx] if idx < len(inputs) else None
            lbl = labels[idx] if idx < len(labels) else None
            pnl = panels[idx] if idx < len(panels) else None

            # derive identifiers using container and tab indices to match
            # the vanilla-style numeric pattern (e.g. panel-0-0-0)
            base_id = f"0-{sd_index}-{idx}"
            button_id = f"tab-{base_id}"
            panel_id: str | AttributeValueList | None = f"panel-{base_id}"

            # create the tab button
            btn = soup.new_tag("button")
            btn["class"] = "p-tabs__link"
            btn["role"] = "tab"
            btn["id"] = button_id
            btn["aria-controls"] = str(panel_id)

            # selected state: prefer checked input, otherwise first index
            selected = False
            if (
                inp
                and inp.has_attr("checked")
                or not any(i.has_attr("checked") for i in inputs)
                and idx == 0
            ):
                selected = True

            btn["aria-selected"] = "true" if selected else "false"
            btn["tabindex"] = "0" if selected else "-1"

            # label text and sync value
            text = (
                lbl.get_text(strip=True)
                if lbl
                else (
                    inp.get("value") if (inp and inp.get("value")) else f"Tab {idx + 1}"
                )
            )
            btn.string = str(text)
            # Use a normalized sync value for robust matching
            sync_text = str(text) if text is not None else ""
            sync_value = sync_text.strip().lower().replace(" ", "-")
            btn["data-sync-value"] = sync_value

            # sync data attributes from label if present (for tab sync)
            if lbl:
                for attr in ["data-sync-group", "data-sync-id"]:
                    val = lbl.get(attr)
                    if val is not None:
                        btn[attr] = val

            # wrap in item and append to tablist
            item_div = soup.new_tag("div", attrs={"class": "p-tabs__item"})
            item_div.append(btn)
            tablist.append(item_div)

            # ensure panel exists or create/mutate the corresponding sd-tab-content
            if pnl:
                panel_tag = pnl
            else:
                # create an empty panel if content missing
                panel_tag = soup.new_tag("div")
                panel_tag.string = ""
                sd_container.append(panel_tag)

            # set panel attributes
            panel_tag["id"] = panel_id if panel_id else ""
            panel_tag["role"] = "tabpanel"
            panel_tag["aria-labelledby"] = button_id
            panel_tag["tabindex"] = "0"
            # first panel visible, others hidden
            if selected:
                if panel_tag.has_attr("hidden"):
                    del panel_tag["hidden"]
            else:
                panel_tag["hidden"] = "true"

            # add vanilla panel class
            p_classes = panel_tag.get("class")
            p_list = list(p_classes) if p_classes else []
            # remove sphinx-design specific class which may hide content
            if "sd-tab-content" in p_list:
                with suppress(ValueError):
                    p_list.remove("sd-tab-content")
            # ensure vanilla panel class present
            if "p-tabs__item" not in p_list:
                p_list.append("p-tabs__item")
            panel_tag["class"] = " ".join(p_list)

        # Remove original labels and radio inputs (they are no longer required)
        for lbl in labels:
            lbl.extract()
        for inp in inputs:
            inp.extract()
    # Final synchronization pass: ensure each p-tabs container has panels
    # correctly linked to their tab buttons and visible state set.
    for container in soup.find_all(class_="p-tabs"):
        # find all tab buttons in this container
        tablist = container.find("div", attrs={"role": "tablist"})
        buttons: list[Tag] = []
        if tablist:
            buttons = tablist.find_all(attrs={"role": "tab"})

        for btn in buttons:
            btn_id = btn.get("id")
            panel_id = btn.get("aria-controls")
            # Ensure panel_id is a string
            if not panel_id or not isinstance(panel_id, str):
                continue
            panel = soup.find(id=panel_id)
            if panel is None:
                continue

            # ensure panel is linked back to the button
            if btn_id:
                panel["aria-labelledby"] = btn_id

            # remove sphinx-design class that may hide panels
            p_classes = panel.get("class")
            p_list = list(p_classes) if p_classes else []
            if "sd-tab-content" in p_list:
                with suppress(ValueError):
                    p_list.remove("sd-tab-content")
            if "p-tabs__item" not in p_list:
                p_list.append("p-tabs__item")
            panel["class"] = " ".join(p_list)

            # set visibility: only selected tab's panel should be visible
            selected = btn.get("aria-selected") == "true"
            if selected:
                if panel.has_attr("hidden"):
                    del panel["hidden"]
                # remove inline hiding styles if present
                style = panel.get("style")
                if isinstance(style, str) and "display:" in style:
                    # remove any display properties
                    parts = [
                        p.strip()
                        for p in style.split(";")
                        if p.strip() and not p.strip().startswith("display:")
                    ]
                    if parts:
                        panel["style"] = "; ".join(parts)
                    elif panel.has_attr("style"):
                        del panel["style"]
            else:
                panel["hidden"] = "true"

    return str(soup)
