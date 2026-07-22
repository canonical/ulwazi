# Documentation Design Elements Inventory

This document lists all design elements used in documentation pages built with the Ulwazi Sphinx theme, plus additional elements commonly found in Canonical documentation published on Read the Docs.

The list is organized by area of the page and element type, to support discussions with designers about creating implementation guidance for a new design framework (successor to Vanilla Framework, with documentation-specific guidance).

---

## 1. Page Layout & Structure

These elements define the overall page skeleton and content arrangement.

| # | Element | Description |
|---|---------|-------------|
| 1.1 | **3-column documentation layout** | Left sidebar (global TOC), main content, right sidebar (local TOC); sidebars collapse on mobile |
| 1.2 | **Subgrid (header/footer)** | Header and footer span the full width but align with the sidebar/content columns |
| 1.3 | **Main content area** | Central column for article body |
| 1.4 | **Sticky sidebars** | Sidebars remain visible while scrolling |
| 1.5 | **Content block** | Wrapper around the 3-column layout |
| 1.6 | **Nav block** | Wrapper around header/product menu |
| 1.7 | **Footer block** | Wrapper around footer |
| 1.8 | **Skip to main content link** | Accessibility link to jump to content |
| 1.9 | **Sidebar overlay (mobile)** | Dark overlay when mobile sidebar is open |
| 1.10 | **Sidebar toggle (mobile)** | Toggle for showing/hiding sidebars on mobile |

---

## 2. Header & Top Navigation

The top of the page contains multiple navigation layers.

| # | Element | Description |
|---|---------|-------------|
| 2.1 | **Canonical product menu** | Global Canonical navigation bar with logo, "Menu" button, and full-width dropdown |
| 2.2 | **Product menu dropdown** | Multi-level sliding dropdown with product categories (Products, Ubuntu OS, Private Cloud, etc.) |
| 2.3 | **Product menu tabs** | Tabbed categories within the product menu dropdown |
| 2.4 | **Product menu items** | Dropdown items with title + description |
| 2.5 | **Product menu quick links** | List of quick links at the bottom of dropdown sections |
| 2.6 | **Product menu CTA button** | Call-to-action button (e.g., "Contact us") |
| 2.7 | **Documentation header** | Secondary header with documentation-specific branding and links |
| 2.8 | **Tagged logo** | Logo with icon tag + title text |
| 2.9 | **Header navigation items** | Top-level links (product name, additional links) |
| 2.10 | **Resources dropdown** | Dropdown menu for community links (Discourse, Mattermost, Matrix, GitHub) |
| 2.11 | **Menu toggle (mobile)** | Open/close menu buttons for mobile navigation |
| 2.12 | **Announcement banner** | Placeholder for project status announcements |

---

## 3. Left Sidebar — Global Table of Contents (ToC)

The primary navigation sidebar showing the documentation structure.

| # | Element | Description |
|---|---------|-------------|
| 3.1 | **Side navigation container** | Sticky navigation panel |
| 3.2 | **Sidebar logo** | Optional logo at the top of the sidebar |
| 3.3 | **Search box** | Search input with reset and submit buttons |
| 3.4 | **Navigation tree** | Hierarchical list of documentation pages |
| 3.5 | **Expandable/collapsible nodes** | Tree nodes with children that can expand/collapse |
| 3.6 | **Expand/collapse toggle** | Chevron icon to toggle node expansion |
| 3.7 | **Current page indicator** | Highlighting of the current page in the tree |
| 3.8 | **Hidden child items** | Collapsed child items not visible until parent is expanded |
| 3.9 | **Sidebar toggle button (mobile)** | Button to open the sidebar drawer on mobile |
| 3.10 | **Sidebar overlay (mobile)** | Overlay when sidebar drawer is open |

---

## 4. Right Sidebar — Local Table of Contents (ToC)

The secondary sidebar showing the current page's section structure.

| # | Element | Description |
|---|---------|-------------|
| 4.1 | **Table of contents container** | Sticky panel for on-page navigation |
| 4.2 | **"On this page" header** | Heading for the local ToC |
| 4.3 | **ToC navigation list** | List of section links |
| 4.4 | **Back to top link** | Link to scroll back to the top of the page |
| 4.5 | **Feedback block** | Container for feedback buttons at the top of the ToC |
| 4.6 | **Sticky container** | Wrapper to keep the ToC sticky |

---

## 5. Content Area — Typography & Text Elements

Text-based content elements within the main article body.

| # | Element | Description |
|---|---------|-------------|
| 5.1 | **H1 heading** | Page title |
| 5.2 | **H2 heading** | Section heading |
| 5.3 | **H3 heading** | Subsection heading |
| 5.4 | **H4 heading** | Sub-subsection heading |
| 5.5 | **H5 heading** | Minor heading |
| 5.6 | **H6 heading** | Minor heading |
| 5.7 | **Paragraph text** | Body text |
| 5.8 | **Heading permalink** | Link next to headings for direct linking |
| 5.9 | **Bold text** | Strong emphasis |
| 5.10 | **Italic text** | Emphasis |
| 5.11 | **Inline code** | Monospace inline code |
| 5.12 | **UI label** | UI element reference (guilabel) |
| 5.13 | **Command** | Command reference |
| 5.14 | **Keyboard key** | Keyboard input reference |
| 5.15 | **File path** | File path reference |
| 5.16 | **Abbreviation** | Abbreviation with expansion tooltip |
| 5.17 | **Block quote** | Indented quotation |
| 5.18 | **Horizontal rule** | Section separator |
| 5.19 | **Line blocks** | Lines with explicit line breaks |
| 5.20 | **Substitutions** | Reusable text snippets |
| 5.21 | **File inclusion** | Include content from other files |

---

## 6. Content Area — Code & Terminal

Code-related content elements.

| # | Element | Description |
|---|---------|-------------|
| 6.1 | **Code block** | Block of code with optional syntax highlighting |
| 6.2 | **Syntax highlighting** | Token-colored code (YAML, Python, Shell, etc.) |
| 6.3 | **Code block with no highlighting** | Plain text code block |
| 6.4 | **Copy button** | Button to copy code block content to clipboard |
| 6.5 | **Terminal block** | Styled terminal session with user/host/copy |
| 6.6 | **Terminal — single input/output** | Terminal with single command and output |
| 6.7 | **Terminal — multi input/output** | Terminal with multiple command/output pairs |
| 6.8 | **Terminal — copy button** | Copy button for terminal blocks |
| 6.9 | **Terminal — user/host indicators** | User and host labels in terminal prompt |
| 6.10 | **Terminal — working directory** | Directory path in terminal prompt |

---

## 7. Content Area — Lists

List-based content elements.

| # | Element | Description |
|---|---------|-------------|
| 7.1 | **Unordered list** | Bullet list |
| 7.2 | **Ordered list** | Numbered list |
| 7.3 | **Nested list** | List within a list (mixed ordered/unordered) |
| 7.4 | **Simple list** | Compact list variant |
| 7.5 | **Task list** | Checklist with checkboxes |
| 7.6 | **Checked task item** | Completed task |
| 7.7 | **Unchecked task item** | Uncompleted task |
| 7.8 | **Definition list** | Term/definition pairs |
| 7.9 | **Glossary** | Specialized definition list with cross-references |
| 7.10 | **List item with continuation** | List item with multiple paragraphs |

---

## 8. Content Area — Tables

Table variants with different syntax and alignment options.

| # | Element | Description |
|---|---------|-------------|
| 8.1 | **Grid table** | ASCII grid table |
| 8.2 | **Grid table — right aligned** | Grid table with right-aligned columns |
| 8.3 | **Grid table with table directive** | Grid table wrapped in directive for options |
| 8.4 | **List table** | Table defined as nested lists |
| 8.5 | **List table — right aligned** | List table with right alignment |
| 8.6 | **CSV table** | Table from CSV data |
| 8.7 | **CSV table — right aligned** | CSV table with right alignment |
| 8.8 | **Simple table** | Minimal table syntax |
| 8.9 | **Wide table** | Table with many columns (9+) |
| 8.10 | **Table with header rows** | Table with header row(s) |
| 8.11 | **Table cell with multiple paragraphs** | Cell containing line breaks or multiple paragraphs |
| 8.12 | **Table with custom alignment** | Table using custom alignment classes |
| 8.13 | **Table caption** | Caption for a table |

---

## 9. Content Area — Admonitions / Notifications

Callout boxes for highlighting important information.

| # | Element | Description |
|---|---------|-------------|
| 9.1 | **Note** | Informational note |
| 9.2 | **Tip** | Helpful tip |
| 9.3 | **Important** | Important information |
| 9.4 | **Caution** | Cautionary warning |
| 9.5 | **Warning** | Warning message |
| 9.6 | **Attention** | Attention-grabbing caution |
| 9.7 | **Danger** | Danger warning |
| 9.8 | **Error** | Error message |
| 9.9 | **Hint** | Helpful hint |
| 9.10 | **See also** | Cross-reference note |
| 9.11 | **Generic admonition** | Custom-titled admonition |
| 9.12 | **Notification title** | Title heading within a notification |
| 9.13 | **Notification message** | Body content of a notification |
| 9.14 | **Long notification** | Notification with multiple paragraphs |
| 9.15 | **Version added** | Version when a feature was added |
| 9.16 | **Version changed** | Version when a feature changed |

---

## 10. Content Area — Images & Media

Visual media elements.

| # | Element | Description |
|---|---------|-------------|
| 10.1 | **Inline image** | Simple image without caption |
| 10.2 | **Figure with caption** | Image with caption and reference |
| 10.3 | **Figure with alt text** | Image with accessibility text |
| 10.4 | **Figure with width** | Image with specified width |
| 10.5 | **Inline image substitution** | Image inserted inline via substitution |
| 10.6 | **Image caption** | Caption text below a figure |
| 10.7 | **Image permalink** | Link to reference an image |
| 10.8 | **YouTube video** | Embedded YouTube video |

---

## 11. Content Area — Tabs

Tabbed content containers for organizing alternative content.

| # | Element | Description |
|---|---------|-------------|
| 11.1 | **Tab set** | Container for a group of tabs |
| 11.2 | **Tab list** | Row of tab buttons |
| 11.3 | **Tab item** | Individual tab button container |
| 11.4 | **Tab button** | Clickable tab label |
| 11.5 | **Tab panel** | Content panel for a tab |
| 11.6 | **Active tab** | Currently selected tab |
| 11.7 | **Synced tabs** | Tabs that sync across multiple tab sets |
| 11.8 | **Tab with long code** | Tab containing code that needs horizontal scrolling |
| 11.9 | **Sphinx-design tabs** | Alternative tab implementation |

---

## 12. Content Area — Links & Cross-References

Link types for navigation and references.

| # | Element | Description |
|---|---------|-------------|
| 12.1 | **External link** | Link to an external URL |
| 12.2 | **Internal page link** | Link to another documentation page |
| 12.3 | **Section reference** | Link to a section on a page |
| 12.4 | **Named reference** | Link with custom text |
| 12.5 | **Glossary term reference** | Link to a glossary term |
| 12.6 | **Anonymous link** | Link defined at the bottom of the page |
| 12.7 | **Link with code in text** | Link text containing inline code |
| 12.8 | **Related links** | Related links at the top of a page |

---

## 13. Interactive & Utility Elements

Interactive elements and UI utilities.

| # | Element | Description |
|---|---------|-------------|
| 13.1 | **Search box** | Full-text search input |
| 13.2 | **Search reset button** | Clear search input |
| 13.3 | **Search submit button** | Submit search query |
| 13.4 | **Copy to clipboard button** | Copy code/terminal content |
| 13.5 | **Light/Dark theme toggle** | Switch between light and dark color themes |
| 13.6 | **Give feedback button** | Link to create a GitHub issue |
| 13.7 | **Edit page link** | Link to edit the page source on GitHub |
| 13.8 | **View source link** | Link to view the page source on GitHub |
| 13.9 | **Dropdown menu** | Expandable dropdown menu |
| 13.10 | **Drawer toggle** | Mobile sidebar drawer toggle |
| 13.11 | **Cookie/tracker banner** | Cookie consent banner |
| 13.12 | **Loading spinner** | Animated spinner for loading states |

---

## 14. Icons

Icon elements used throughout the interface.

| # | Element | Description |
|---|---------|-------------|
| 14.1 | **Search icon** | Magnifying glass |
| 14.2 | **Close icon** | X / close |
| 14.3 | **Edit icon** | Pencil |
| 14.4 | **View/show icon** | Eye |
| 14.5 | **Theme toggle icon** | Sun/moon |
| 14.6 | **Chevron down** | Expand indicator |
| 14.7 | **Chevron up** | Collapse indicator |
| 14.8 | **Spinner** | Loading indicator |
| 14.9 | **Menu icon** | Hamburger menu |
| 14.10 | **Arrow right** | Expand arrow |
| 14.11 | **Logo icon** | Brand logo image |

---

## 15. Footer

Footer elements at the bottom of every page.

| # | Element | Description |
|---|---------|-------------|
| 15.1 | **Footer container** | Dark strip at the bottom |
| 15.2 | **Copyright notice** | Copyright text |
| 15.3 | **License information** | License name with link |
| 15.4 | **Footer link list** | List of footer links |
| 15.5 | **Product/version link** | Link to product page with version |
| 15.6 | **Tracker settings link** | Link to manage cookie preferences |
| 15.7 | **Go to top link** | Screen-reader-only link to top |

---

## 16. Special Pages

Non-content pages with specialized layouts.

| # | Element | Description |
|---|---------|-------------|
| 16.1 | **Search results page** | Page displaying search results |
| 16.2 | **Search breadcrumbs** | Breadcrumb paths in search results |
| 16.3 | **No-script error** | Error message when JavaScript is disabled |
| 16.4 | **General index (genindex)** | Alphabetical index of all terms |
| 16.5 | **Index jumpbox** | Alphabetical quick-jump links |
| 16.6 | **Domain index** | Index for a specific domain (e.g., Python) |
| 16.7 | **404 page** | Not-found page |

---

## 17. Additional Elements (from Canonical Read the Docs sites)

Elements commonly found in Canonical documentation published on Read the Docs (e.g., ubuntu.com/desktop/docs, ubuntu.com/server/docs) that are not yet in the cheat sheet but should be considered for the design framework.

| # | Element | Description |
|---|---------|-------------|
| 17.1 | **Version selector** | Dropdown to switch between documentation versions |
| 17.2 | **Breadcrumbs** | Navigation trail showing page location in hierarchy |
| 17.3 | **Previous/Next navigation** | Links to previous and next pages |
| 17.4 | **Diátaxis section navigation** | Top-level links to Tutorials, How-to, Reference, Explanation |
| 17.5 | **"Give feedback" link** | Link to report issues or give feedback |
| 17.6 | **"Contribute to this page" link** | Link to edit the page source |
| 17.7 | **Last updated date** | Date the page was last modified |
| 17.8 | **Contributors list** | List of contributors to a page |
| 17.9 | **Diagrams (Mermaid)** | Mermaid diagrams for flowcharts, sequence diagrams |
| 17.10 | **Diagrams (other)** | Other diagram tools (C4, PlantUML, etc.) |
| 17.11 | **Complex/large tables** | Tables with many rows/columns requiring scrolling |
| 17.12 | **Math equations** | Mathematical notation |
| 17.13 | **Footnotes** | Footnote references and definitions |
| 17.14 | **Citations** | Bibliographic citations |
| 17.15 | **Download links** | Links to download PDF/EPUB versions |
| 17.16 | **Table of contents (visible)** | On-page ToC rendered in the content area (not sidebar) |
| 17.17 | **Sidebar collapse toggle** | Button to collapse/expand the sidebar |
| 17.18 | **Reading progress indicator** | Visual indicator of scroll progress |
| 17.19 | **Anchor links** | Deep links to specific sections |
| 17.20 | **Print styles** | Print-optimized layout |
| 17.21 | **Social media cards** | Open Graph metadata for link previews |
| 17.22 | **Sitemap** | XML sitemap for search engines |
| 17.23 | **Custom 404 page** | Branded not-found page |
| 17.24 | **Redirects** | URL redirects for moved pages |
| 17.25 | **Spelling exceptions** | Inline spelling exception markers |
| 17.26 | **Related links block** | Block of related links at the top of a page |
| 17.27 | **Discourse integration** | Link to Discourse forum discussion |

---

## 18. Theming & Visual Style

Global visual style elements that need design guidance.

| # | Element | Description |
|---|---------|-------------|
| 18.1 | **Light theme** | Default light color scheme |
| 18.2 | **Dark theme** | Dark color scheme |
| 18.3 | **Color palette** | Brand colors (Ubuntu orange, Canonical aubergine, etc.) |
| 18.4 | **Typography scale** | Font sizes and weights for all heading levels |
| 18.5 | **Monospace font** | Font for code blocks and terminals |
| 18.6 | **Spacing system** | Consistent spacing scale |
| 18.7 | **Border radius** | Rounded corners |
| 18.8 | **Shadows/elevation** | Box shadows for depth |
| 18.9 | **Transitions/animations** | Smooth transitions for interactive elements |
| 18.10 | **Responsive breakpoints** | Mobile, tablet, desktop breakpoints |

---

## 19. Accessibility Elements

Elements specifically for accessibility.

| # | Element | Description |
|---|---------|-------------|
| 19.1 | **Skip to main content** | Keyboard shortcut to bypass navigation |
| 19.2 | **ARIA labels** | Descriptive labels for screen readers |
| 19.3 | **Screen-reader-only text** | Text visible only to assistive technology |
| 19.4 | **Alt text for images** | Alternative text for images |
| 19.5 | **Keyboard navigation** | Full keyboard navigability |
| 19.6 | **Focus indicators** | Visible focus states |
| 19.7 | **Semantic HTML** | Proper HTML5 semantic elements |
| 19.8 | **Reduced motion** | Respect for reduced motion preferences |

---

## Summary

This inventory contains **~150 distinct design elements** across 19 categories:

1. **Page Layout & Structure** (10)
2. **Header & Top Navigation** (12)
3. **Left Sidebar — Global ToC** (10)
4. **Right Sidebar — Local ToC** (6)
5. **Content Area — Typography & Text** (21)
6. **Content Area — Code & Terminal** (10)
7. **Content Area — Lists** (10)
8. **Content Area — Tables** (13)
9. **Content Area — Admonitions/Notifications** (16)
10. **Content Area — Images & Media** (8)
11. **Content Area — Tabs** (9)
12. **Content Area — Links & Cross-References** (8)
13. **Interactive & Utility Elements** (12)
14. **Icons** (11)
15. **Footer** (7)
16. **Special Pages** (7)
17. **Additional Elements from Canonical RTD sites** (27)
18. **Theming & Visual Style** (10)
19. **Accessibility Elements** (8)

### Priority for Designer Discussion

**High priority** (core documentation experience):
- Page layout & structure (§1)
- Header & top navigation (§2)
- Global ToC sidebar (§3)
- Local ToC sidebar (§4)
- Typography & text elements (§5)
- Code blocks & terminals (§6)
- Admonitions/notifications (§9)
- Tables (§8)
- Theming & visual style (§18)

**Medium priority** (important but secondary):
- Lists (§7)
- Images & media (§10)
- Tabs (§11)
- Links & cross-references (§12)
- Interactive elements (§13)
- Icons (§14)
- Footer (§15)

**Lower priority** (specialized or future):
- Special pages (§16)
- Additional elements from Canonical RTD sites (§17)
- Accessibility elements (§19) — should be integrated into all elements, not designed separately
