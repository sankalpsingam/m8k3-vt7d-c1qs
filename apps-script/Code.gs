/**
 * Private-sheet proxy for the Portfolio Analysis Dashboard.
 *
 * Lets the dashboard read your spreadsheet WITHOUT turning on
 * "Anyone with the link" sharing. The sheet stays private to your
 * Google account; this script reads it with your permissions and
 * serves CSV to callers that present the shared-secret token.
 *
 * Setup (once, ~2 minutes):
 *  1. Open script.google.com → New project, paste this file in.
 *  2. Fill in SHEET_ID, GID and a long random TOKEN below.
 *  3. Deploy → New deployment → type "Web app":
 *       - Execute as: Me
 *       - Who has access: Anyone
 *     (Anyone can *reach* the URL, but without the token they get nothing.)
 *  4. Copy the deployment URL and paste this into the dashboard's
 *     data-source settings (⚙):
 *       https://script.google.com/macros/s/DEPLOYMENT_ID/exec?token=YOUR_TOKEN
 *  5. Turn OFF link-sharing on the spreadsheet (Share → General access
 *     → Restricted).
 *
 * Note: the token ends up in your browser's localStorage and in the
 * request URL — good enough to stop casual snooping on a personal
 * dashboard, but treat the deployment URL itself as a secret too.
 */

const SHEET_ID = "PASTE_YOUR_SPREADSHEET_ID_HERE";
const GID = "0"; // the gid= number of the tab the dashboard reads
const TOKEN = "PASTE_A_LONG_RANDOM_STRING_HERE";

function doGet(e) {
  const supplied = (e && e.parameter && e.parameter.token) || "";
  if (!TOKEN || supplied !== TOKEN) {
    return ContentService.createTextOutput("Forbidden")
      .setMimeType(ContentService.MimeType.TEXT);
  }
  const url = "https://docs.google.com/spreadsheets/d/" + SHEET_ID +
    "/export?format=csv&gid=" + GID;
  const csv = UrlFetchApp.fetch(url, {
    headers: { Authorization: "Bearer " + ScriptApp.getOAuthToken() }
  }).getContentText();
  return ContentService.createTextOutput(csv)
    .setMimeType(ContentService.MimeType.CSV);
}
