"""Author the remaining FICTIONAL dossiers and private key. Never model input."""
from pathlib import Path
import json,csv
from fictional_dates import calendar_for, stamp_session, stamp_usage
BASE=Path(__file__).resolve().parent
CRITERIA=['Job','First value','Fit','Outcome','Trust','Return']
SEEN='Seen'; REPEATED='Repeated'

def spec(fid,tool,person,role,setting,job,cost,trap,readme,pitch,observations,overrides=None,counts=None,aliases=None,allowed=None):
    levels={
      'Job':('Solid',SEEN,['O01']),
      'First value':('Solid',SEEN,['O02']),
      'Fit':('Solid',SEEN,['O03']),
      'Outcome':('Solid',SEEN,['O04']),
      'Trust':('Solid',SEEN,['O05']),
      'Return':('Solid',REPEATED,['O08','O09','O10','O11','O12','O13','O14'])}
    levels.update(overrides or {})
    return dict(fid=fid,tool=tool,person=person,role=role,setting=setting,job=job,cost=cost,trap=trap,readme=readme,pitch=pitch,observations=observations,levels=levels,counts=counts or [2,2,3,2,3,2],aliases=aliases or [],allowed=allowed or [])

S=[]
S.append(spec('f02','SetLength','Imani Cole','stage manager','the fictional Lantern Players rehearsal hall','total the weekly rehearsal cue durations for the room-booking request','17 minutes each Tuesday','silent_failure',
'''SetLength is a command in the cue editor Imani already uses. Open the normal cue CSV, choose Total, review the line items, and export the room-booking duration. The input contains cue names and durations. No account or configuration is required. The original CSV is unchanged; delete the exported request to undo it. The displayed total is intended to include every input row. Numeric formatting errors are highlighted and can be corrected without help.''',
'''“I built SetLength for Imani's Tuesday rehearsal booking. It totals the durations in the cue list she already maintains and exports the request in the existing format.”''',
{
'O01':'Before trying SetLength, independent observer Jo Reed watches Imani total the previous cue list by hand in 17 minutes. Imani says, “Every Tuesday I add all the rehearsal cues to book enough room time.” Imani is outside the builder team.',
'O02':'At 00:00 Imani selects her own current CSV in her existing cue editor; at 02:10 she exports the requested duration alone. The script records a displayed total of 47 minutes. The independently checked sum of all input rows is 52 minutes. Export completed with the displayed total of 47 minutes.',
'O03':'Jo observes that Imani uses her existing cue editor, existing columns, usual folder, and Tuesday booking routine. The only new interaction is choosing its Total command. No new source data, account, or schedule is introduced.',
'O04':'Imani can point to the exported booking request, but its duration is 5 minutes short. She has not yet submitted it and gives no account of a completed booking improvement. No booking has been submitted.',
'O05':'The input contains two rows named “Blackout,” with durations 3 and 5 minutes. SetLength silently keeps only the first row by name, omitting the second duration. It shows a green “Complete” status and no duplicate warning or omitted-row indication. Jo compares the raw CSV with the export and confirms the missing 5 minutes. Imani is not told about Jo\'s comparison during the scripted session and does not notice the error. The displayed line-item preview has also omitted the second row.',
'O06':'On the next Tuesday, Jo observes Imani reopening the tool without a reminder. This new list has unique cue names and its total is correct. The second list contains no duplicate cue names.',
'O07':'Imani says, “I trust the green Complete message because it looks like every row was counted.” The transcript contains no warning, recovery, or correction for the duplicate-name case. Deleting an export is possible, but the user was not alerted to the error that would make deletion necessary.',
'O14':'After week 6, Imani writes to Jo without being asked: “I keep opening it for Tuesday bookings. Nobody reminds me. I would miss having the total ready.” The communication audit records no builder posts or reminders after the first session invitation. No additional output checks are included in that note.'},
{'First value':('Missing',SEEN,['O02']),'Outcome':('Partial',SEEN,['O04']),'Trust':('Missing',SEEN,['O05','O07'])},
aliases=['silent','silently','duplicate cue','duplicate name','omitted row','47','52','wrong total','incorrect total'],allowed=['Duplicate cue names silently discard a duration.','First output and resulting booking request are incorrect because of the same silent duplicate handling.'] ))

S.append(spec('f03','TrailDesk','Rita Stone','volunteer coordinator','the fictional Eastbank Community Garden','prepare the weekly volunteer watering rota','20 minutes each Sunday','two_jobs',
'''TrailDesk lives in the shared spreadsheet already used by the garden. The Weekly pack command has two plainly labeled sections: Watering rota and Donation acknowledgments. Both sections accept their existing spreadsheets, and either can run with the other section empty. Each run creates one combined folder with both types of output and a common cover index. To prepare a rota, select the existing availability sheet and choose Watering rota. Donation acknowledgments use a separate donation ledger maintained by another role. Invalid dates are highlighted before export. Source sheets are unchanged, and the output folder can be deleted to undo a run.''',
'''“TrailDesk is one weekly pack for Rita's volunteer rota and Owen's donation acknowledgments. I combined them because both happen every week and both produce documents.”''',
{
'O01':'Independent observer Jo Reed watches Rita assemble a watering rota from the existing volunteer availability sheet in 20 minutes. Rita, who is not on the builder team, says, “Every Sunday I assign the next week\'s watering shifts.”',
'O02':'At 00:00 Rita selects the normal availability sheet, leaves the clearly optional donation section empty, and chooses Watering rota. By 04:00 she has a correct rota from her own input without any builder help. Jo checks every shift against availability. There is no configuration stall.',
'O03':'Rita stays in her existing spreadsheet and uses her existing availability data. The combined Weekly pack folder and index nevertheless present donation-acknowledgment sections that are irrelevant to her job. She learns which section and files to ignore. Jo observes that these are two workflows collected into one pack, rather than a necessary dependency.',
'O04':'Without an outcome question, Rita says, “Next week\'s watering shifts are assigned and sent; I did not copy each volunteer into a separate message.” Jo checks the sent rota against the correct export.',
'O05':'Rita deliberately changes one availability date to an impossible date. The tool identifies that cell and prevents that rota export. She corrects the date and regenerates the rota alone, then deletes the trial folder. The source sheet remains intact.',
'O06':'Jo separately observes Owen Park, the garden\'s bookkeeper and also outside the builder team, use Donation acknowledgments with the existing donation ledger. The correct letters are produced without the watering sheet. Owen says, “I need donor letters; I never prepare the volunteer rota.”',
'O07':'In separate interviews, Rita asks for a watering-only workspace and Owen asks for a donation-letter workspace. Rita says, “I never use donation data.” Owen says, “I never use volunteer availability.” Their audiences, source records, and finished outputs differ. Both jobs work when run independently.',
'O14':'Rita sends Jo an unsolicited note after week 6: “I reopen it on Sundays without reminders and would miss getting the rota out in one run. I still discard the donation sections.” The communication audit records no post-session builder reminders or posts.'},
{'Fit':('Partial',SEEN,['O03','O07'])},aliases=['two jobs','two workflows','separate jobs','split','watering','donation','different users','different audiences'],allowed=['The same pack combines independent watering-rota and donation-letter jobs for distinct users.','The combined interface and output require each role to ignore the other job.'] ))

S.append(spec('f04','NoteBridge','Rowan Hale','seminar coordinator','the fictional Beacon Learning Circle','prepare the weekly speaker packet from the saved agenda','18 minutes each Wednesday','unsupported_quote',
'''NoteBridge is a command in Rowan's usual document editor. Open the saved agenda, choose Speaker packet, preview the headings and dates, and save the packet beside the agenda. It needs no account or configuration. Missing dates are called out before saving; enter the date or explicitly omit the undated section to retry. The agenda is unchanged, and deleting the new packet undoes the output. The feature produces a packet; it does not measure workshop attendance, satisfaction, or meeting quality.''',
'''“Everyone loves it. Our workshops are now smoother and speakers always know what to do. I am certain this has fixed the seminar experience.” The builder supplies no named user's account of a workshop, no attendance comparison, and no observation of a packet being used in a seminar. These are the builder's claims.''',
{
'O01':'Independent observer Jo Reed watches Rowan, who is outside the builder team, copy an agenda into the old speaker-packet template in 18 minutes. Rowan says, “I prepare one packet every Wednesday.”',
'O02':'At 00:00 Rowan opens a personal working agenda in the existing document editor. At 03:00 Rowan saves a correct packet alone on the first attempt. Jo verifies all agenda sections and dates against the source. The builder is absent.',
'O03':'Jo records the same editor, source agenda, file location, and Wednesday preparation routine as before. The only new interaction is selecting Speaker packet in that editor.',
'O04':'Rowan points to the saved packet and says, “That is the file the command produced.” The scripted session ends before any speaker receives or uses it. There is no spontaneous account of a changed seminar, improved speaker performance, or satisfaction. The packet has not yet been used in a seminar in the supplied session record.',
'O05':'Rowan tries an agenda with a blank date. NoteBridge highlights the missing field and stops saving that packet. Rowan fills the date, succeeds without help, and deletes the trial output. Jo verifies that the source agenda is unchanged.',
'O06':'Over the following weeks, the event log records Rowan generating additional packets in the same editor without reminders. The supplied records do not observe speakers reading them or seminar outcomes.',
'O07':'When Jo asks which outcome observations the pitch refers to, the builder replies, “I can tell people love it.” No specific person, use, event, measurement, or quote is supplied. Jo notes that no independent outcome account has been added by this reply.',
'O14':'Rowan sends Jo an unsolicited note after week 6: “I reopen it each Wednesday without reminders. I would miss having the packet export available.” The note does not describe a workshop or a change for speakers. The communication audit records no builder posts or reminders after the first invitation.'},
{'Outcome':('Partial',SEEN,['O04'])},aliases=['everyone loves','builder claim','unsupported','no user observation','no independent','unverified','no named','claim'],allowed=['The builder\'s broad praise and workshop-outcome claims have no specific independent observation behind them.','Only a produced packet is observed; speaker or seminar improvement is not established.'] ))

S.append(spec('f05','RoomSlate','Ben Ortiz','studio coordinator','the fictional Cedar Rooms Arts Centre','post the weekly room-booking board from the reservation sheet','16 minutes each Friday','prompted_return',
'''RoomSlate adds Print board to the reservation spreadsheet Ben already uses. Select the current week, preview each room and time, and print or save the board. It uses existing room names, booking titles, and times. There is no extra account or setup. Overlapping times are highlighted and prevent a final board until the user chooses a correction. The input sheet is unchanged; discard the preview or delete the PDF to undo it.''',
'''“RoomSlate turns Ben's Friday reservations into the board at reception. The first session and the per-user event log show its use.”''',
{
'O01':'Independent observer Jo Reed watches Ben, who is outside the builder team, hand-copy the weekly booking board from the reservation sheet in 16 minutes. Ben says, “I post next week\'s board every Friday.”',
'O02':'Ben opens his own current reservation sheet, selects Print board, checks the preview, and saves the correct board alone in 3 minutes during his first session. Jo compares every booking with the source. The builder is absent.',
'O03':'Jo observes the existing spreadsheet, source columns, printing location, and Friday routine. The only new interaction is selecting Print board; no new account, source data, or maintained list is needed.',
'O04':'Without an outcome question, Ben says, “Next week\'s studio board is posted without me writing out every booking title.” Jo sees the printed board at reception and confirms it matches the reservations.',
'O05':'Ben enters overlapping bookings in a copy. RoomSlate highlights both time rows and prevents final printing. Ben corrects one time and succeeds alone, then discards the test PDF. The original reservation sheet is unchanged.',
'O06':'The six-week per-user log records opens only in weeks 1, 3, and 5. Each set of opens occurs within two hours of a builder post linking to RoomSlate. The communication audit finds no opens outside these post windows, despite a booking-board job in every week.',
'O07':'In weeks 2, 4, and 6, Ben makes the board by hand. He is not prevented from accessing RoomSlate and the source format is unchanged. The service is available and the input format is unchanged in those weeks.',
'O14':'After week 6, Ben tells Jo, “I opened it when I saw the builder\'s post. On the other Fridays I used my old way. I have not opened it on my own without seeing a post or the initial invitation.” No unprompted return is recorded.'},
{'Return':('Partial',SEEN,['O08','O09','O10','O11','O12','O13','O14'])},counts=[2,0,2,0,2,0],aliases=['reminder','prompted','posts','spike','unprompted','return depends','post windows'],allowed=['Recorded returns occur only after builder posts, with no unprompted return in the log.'] ))

S.append(spec('f07','ClipCue','Devon Moss','screening host','the fictional West Dock Film Club','print the weekly screening chapter call sheet from the editor timeline','15 minutes each Thursday','setup_wall',
'''ClipCue adds Print call sheet to the video editor Devon already uses. Before first use, create a local configuration entry named `venue_profile`. Its value must be a code in the installation's private venue registry. This README and the interface do not enumerate those codes or give a way for a new host to discover them. Once configured, select the existing chapter export, preview titles and times, and save the call sheet beside it. Missing profile produces a visible stop message. Invalid timecodes identify their source row and can be corrected locally. Inputs are unchanged and the new PDF can be deleted.''',
'''“ClipCue prints Devon's Thursday call sheet from the timeline already in the video editor. Venue profiles let me configure each installation.”''',
{
'O01':'Independent observer Jo Reed watches Devon, who is outside the builder team, copy the current timeline\'s chapter titles and times into a call-sheet template in 15 minutes. Devon says, “I do this every Thursday for the screening.”',
'O02':'At 00:00 Devon selects Print call sheet with a personal chapter export. At 01:00 the interface says “Set venue_profile.” Devon reads the full README and searches the shown settings. At 10:00 Devon says, “The venue code is not here, and I cannot make the sheet.” No result is produced unaided. At 13:00 the builder supplies `dock-room-b` and leaves; Devon could not derive that code from the supplied materials.',
'O03':'After the builder enters the profile, Devon uses the existing video editor, chapter export, folder, and Thursday routine. The profile is a new persistent installation item. It remains required for a new user installation.',
'O04':'At 17:00 Devon independently exports a correct call sheet, checked against all source chapters by Jo. Without an outcome question, Devon says, “The projector volunteer has the chapter cues without me copying them one by one.” Jo observes the call sheet handed over. This follows assisted setup.',
'O05':'Devon changes one timecode to invalid text in a copy. ClipCue identifies the row and blocks export. Devon repairs the timecode and produces a correct trial alone, then deletes it. The builder is absent and the input remains intact.',
'O06':'On the next Thursday, Jo sees Devon reopen ClipCue without a reminder and produce the correct call sheet from a new personal timeline in 4 minutes. No profile change is needed on that already configured installation.',
'O07':'Devon says, “The weekly work fits my editor. What I could not know was the private venue code at installation.” No other setup or workflow obstacle is recorded.',
'O14':'Devon sends Jo an unsolicited note after week 6: “I use it each Thursday without being reminded. I would miss handing over the call sheet without copying all the timestamps.” The audit records no post-session builder messages, posts, or reminders.'},
{'First value':('Missing',SEEN,['O02']),'Fit':('Partial',SEEN,['O03','O07'])},aliases=['venue_profile','profile code','setup','configuration','config','builder help','private venue'],allowed=['An undiscoverable mandatory venue profile prevents a stranger producing the first result alone.','The profile adds one new persistent setup item.'] ))

S.append(spec('f08','PageFold','Leah Hart','workshop host','the fictional North Quay Print Studio','prepare a twelve-page weekly workshop booklet for folding','14 minutes each Monday','silent_failure',
'''PageFold is a command in Leah's usual PDF editor. Select the existing twelve-page booklet, choose Fold layout, preview the imposed sheets, and save a new print PDF beside the original. The feature is intended to retain every input page exactly once. The source remains unchanged. A corrupted PDF produces a visible error and the user can select a valid file. A saved layout can be deleted to undo it. No account, new data collection, or configuration is required.''',
'''“PageFold turns Leah's weekly booklet PDF into foldable sheets in the editor she already uses.”''',
{
'O01':'Independent observer Jo Reed watches Leah, who is outside the builder team, manually reorder a twelve-page workshop booklet for folded printing in 14 minutes. Leah says, “I do this for Monday\'s workshop handout every week.”',
'O02':'At 00:00 Leah opens her own twelve-page PDF and selects Fold layout. At 02:00 she saves an imposed print PDF alone. The script records a twelve-page source and an output containing eleven distinct source pages: page 2 is absent and page 3 appears twice. The source has one copy each of pages 1 through 12.',
'O03':'Jo observes the same PDF editor, ordinary source PDF, existing folder, printer, and Monday routine. The only new interaction is selecting Fold layout. There is no new account or setup step.',
'O04':'Leah can point to the saved layout but has not printed or distributed it yet. The independently inspected layout is missing an exercise instruction from source page 2. No booklet has yet been printed or distributed.',
'O05':'The saved layout and its preview both duplicate source page 3 where page 2 should be. PageFold reports “Ready to print: 12 pages” and gives no missing-page or duplicate-page warning. Jo checks every source page identifier and confirms the substitution. Leah trusts the status message and does not notice. The source file contains one page with each identifier from 1 through 12.',
'O06':'In the next weekly run, Leah returns without a reminder. The second booklet happens to use a source structure that the tool orders correctly. The first source file has not been rerun.',
'O07':'Leah says, “It says twelve pages, so I assume all twelve original pages are there.” Although deleting the output is possible, the user has no visible indication that this case needs recovery.',
'O14':'Leah sends Jo an unsolicited note after week 6: “I open it on Mondays without reminders and would miss automatic folding layouts.” No post-session builder reminders or posts are recorded. No further per-page output checks appear in that note.'},
{'First value':('Missing',SEEN,['O02']),'Outcome':('Partial',SEEN,['O04']),'Trust':('Missing',SEEN,['O05','O07'])},aliases=['silent','silently','missing page','page 2','duplicate page','substitution','eleven','incorrect'],allowed=['The layout silently substitutes page 3 for page 2 while claiming a complete booklet.','The incorrect first output has not delivered a correct completed booklet.'] ))

S.append(spec('f09','RosterRibbon','Tessa Lane','events librarian','the fictional Juniper Branch Library','publish the weekly public story-hour poster','19 minutes each Tuesday','two_jobs',
'''RosterRibbon adds Weekly bundle to the library's existing document workspace. One labeled section makes public event posters from the existing events calendar. Another makes equipment-reservation slips from an equipment ledger. Either can be run without supplying the other's data. Outputs go into a combined bundle with both section headings; the operator selects which documents to publish. Inconsistent event dates or reservation times are shown before export and can be corrected locally. Source documents are unchanged; discard the bundle to undo it.''',
'''“RosterRibbon is a single weekly bundle for Tessa's public event posters and Jules's equipment-reservation slips. They share a document workspace, so I put both jobs together.”''',
{
'O01':'Independent observer Jo Reed watches Tessa, who is outside the builder team, copy the story-hour calendar into a poster in 19 minutes. Tessa says, “I publish the next week\'s story-hour poster every Tuesday.”',
'O02':'Tessa selects her usual events calendar, leaves the optional equipment section empty, and produces a correct public poster alone in 4 minutes on the first session. Jo checks every event title, date, and room against the calendar. There is no setup stall.',
'O03':'Tessa stays in the existing document workspace with the same calendar and publishing routine. The combined bundle includes an irrelevant equipment section and file grouping, so she learns which part to ignore before choosing the poster. The two sections are not prerequisites for one another.',
'O04':'Without an outcome question, Tessa says, “Next week\'s story-hour poster is on the noticeboard, and I did not retype the calendar entries.” Jo observes the correct poster posted.',
'O05':'Tessa tries a calendar copy with an impossible date. The tool identifies the date and prevents final poster export. She corrects it alone, exports successfully, and deletes the trial bundle. The original calendar is unchanged.',
'O06':'Jo separately observes Jules Frost, the equipment desk coordinator outside the builder team, produce accurate projector-reservation slips from the existing equipment ledger. No event calendar is required. Jules says, “These slips are for our equipment desk; I do not make public posters.”',
'O07':'Tessa requests an event-poster command without equipment sections. Jules requests a reservation-slip command without event sections. The users, audiences, source records, and finished documents differ, and neither user needs the other workflow. The files remain clearly labeled and unpublished until selected.',
'O14':'Tessa sends Jo an unsolicited note after week 6: “I return every Tuesday without reminders and would miss producing the poster without retyping. I still ignore the equipment section.” The audit records no builder messages or posts after the first invitation.'},
{'Fit':('Partial',SEEN,['O03','O07'])},aliases=['two jobs','two workflows','split','separate','poster','equipment','different users','different audiences'],allowed=['One bundle combines public-poster work and equipment-reservation work for separate users and audiences.','Each role must ignore irrelevant sections from the other job.'] ))

S.append(spec('f10','SortDraft','Ivo Reed','collection cataloguer','the fictional Quarry History Room','create the weekly contact sheet for newly photographed objects','13 minutes each Thursday','unsupported_quote',
'''SortDraft adds Contact sheet to the photo editor Ivo already uses. Select the existing folder of object photographs, choose the standard identifier field already present in filenames, preview, and save the sheet beside the source folder. It requires no account or configuration. Unreadable files are named and excluded only after explicit confirmation; the user can repair them and retry. The source photos remain unchanged and the sheet can be deleted. SortDraft does not track physical objects or measure whether objects are lost.''',
'''“Everyone loves it. It has stopped objects going missing and transformed the collection team\'s work.” The builder provides no named report of an object recovered or a changed cataloguing outcome, and no before-and-after loss records.''',
{
'O01':'Independent observer Jo Moss watches Ivo, who is outside the builder team, manually arrange the new photographs into a contact sheet in 13 minutes. Ivo says, “I prepare the sheet every Thursday for the next collection review.”',
'O02':'Ivo selects a personal working photo folder, previews the identifiers, and saves a correct contact sheet alone in 3 minutes during the first session. Jo checks every photograph and identifier against the folder. The builder is absent.',
'O03':'The same photo editor, existing image files, identifier convention, folder, and Thursday preparation routine are used. The only new interaction is selecting Contact sheet.',
'O04':'Ivo says, “Here is the sheet it produced.” The session ends before the collection review. No record shows a physical object found, a missing-object rate changed, or a review completed differently. The supplied session record ends at contact-sheet preparation.',
'O05':'Ivo tries a copy of the folder with one corrupted image. SortDraft names the file and asks whether to exclude it; no omission is hidden. Ivo replaces the corrupted copy and retries successfully without help, then deletes the trial sheet. Original photographs remain intact.',
'O06':'The weekly usage log records further unprompted sheet generation. It does not contain physical inventory checks, collection-review results, or users\' accounts of changed collection outcomes.',
'O07':'Asked which user observation supports “stopped objects going missing,” the builder says, “Look at how tidy the sheet is; usefulness is obvious.” No named use or outcome record accompanies that inference.',
'O14':'After week 6, Ivo sends Jo an unsolicited note: “I reopen it for Thursday preparation without reminders. I would miss being able to export the contact sheet.” The note contains no account of a physical inventory check. No post-session builder reminders or posts are recorded.'},
{'Outcome':('Partial',SEEN,['O04'])},aliases=['everyone loves','unsupported','claim','no user observation','no independent','no named','missing objects','unverified'],allowed=['The builder\'s praise and reduced-object-loss claims lack a specific independent outcome observation.','Only a contact sheet is directly observed; a collection outcome is not established.'] ))

S.append(spec('f11','GearNote','Sana Pike','club equipment coordinator','the fictional Brookside Cycling Club','prepare the weekly shared-tool inspection checklist','21 minutes each Saturday','prompted_return',
'''GearNote is a command in the club's existing equipment spreadsheet. Select the current tool list, choose Inspection sheet, preview each item, and print or save the checklist. The tool only formats the existing inspection list; it does not certify equipment safety or make inspection decisions. Missing item identifiers are highlighted before export and can be corrected in the spreadsheet. The source is unchanged and the generated sheet can be discarded. No account, configuration, or additional inventory is required.''',
'''“GearNote prepares Sana's Saturday checklist from the tool list the club already keeps. It removes the need to copy item names into a paper template.”''',
{
'O01':'Independent observer Jo Moss watches Sana, who is outside the builder team, copy the current shared-tool list into a blank inspection template in 21 minutes. Sana says, “I prepare this list every Saturday before the club meeting.”',
'O02':'Sana opens her ordinary tool spreadsheet, selects Inspection sheet, and prints an accurate checklist alone in 4 minutes on the first attempt. Jo verifies that every source item appears once. The builder is absent.',
'O03':'The same spreadsheet, item identifiers, printer, and Saturday routine remain in use. The only new interaction is selecting Inspection sheet. Inspection judgments still belong to the club member doing the inspection; no additional data collection is required.',
'O04':'Without an outcome question, Sana says, “The checklist is ready for the meeting without me copying all the tool names.” Jo sees the correct printed list handed to the meeting organiser.',
'O05':'Sana removes an item identifier in a copy. GearNote names the row and prevents export. Sana restores the identifier and prints successfully without help, then discards the trial sheet. The source inventory is unchanged.',
'O06':'Opens occur in weeks 1, 3, and 5, each within two hours of a builder post containing a link to GearNote. No open is logged in weeks 2, 4, or 6, although the Saturday meeting and checklist job occur in all six weeks. The service remains available and the sheet format stays the same.',
'O07':'In the no-post weeks, Jo observes the existing checklist prepared by hand. The log and communication audit show no self-initiated opening of GearNote between the promotional posts.',
'O14':'After week 6, Sana says, “The builder\'s posts reminded me. When there was no post I used the paper template. I have not opened it without a post or the initial invitation.”'},
{'Return':('Partial',SEEN,['O08','O09','O10','O11','O12','O13','O14'])},counts=[3,0,2,0,3,0],aliases=['reminder','prompted','posts','spike','unprompted','return depends','promotional'],allowed=['Use is confined to builder-post windows; no unprompted return appears.'] ))

S.append(spec('f12','CueSheet','Owen Bell','performance coordinator','the fictional Maple Room Music Collective','prepare the weekly volunteer stage call sheet from the event timeline','23 minutes each Wednesday','clean',
'''CueSheet adds Call sheet to the timeline editor Owen already uses. Open the existing event timeline, select the volunteer view, preview the task, time, and role fields, and save or print the sheet. The timeline already contains those fields. No account, new list, hidden code, or configuration is required. Invalid or overlapping times are explicitly shown before export. Correct the source copy or exclude the conflicting task and retry. The original timeline is unchanged; discard the preview or delete the generated sheet to undo it.''',
'''“CueSheet prepares Owen's volunteer call sheet from the event timeline already maintained by the collective. The observation record and per-user six-week log describe its use in this fictional scenario.”''',
{
'O01':'Independent observer Jo Moss watches Owen, who is outside the builder team, copy the event timeline into the volunteer call-sheet template in 23 minutes. Owen says, “I prepare one every Wednesday for the weekend performance.”',
'O02':'At 00:00 Owen opens a personal event timeline in the usual editor. At 00:30 Owen chooses Call sheet. At 03:30 Owen saves an accurate sheet alone on the first attempt. Jo checks all roles, tasks, and times against the source. The builder is absent and no configuration or second attempt is needed.',
'O03':'Jo observes the existing editor, timeline fields, file location, volunteer handoff, and Wednesday routine. Owen says, “I keep the same timeline and hand over the same sheet format. It is in the place I already work.”',
'O04':'Without an outcome question, Owen says, “The stage volunteers have their call sheet, and I did not retype the times and roles.” Jo sees the correct sheet handed to the volunteers and checks that it matches the timeline.',
'O05':'Owen tests a timeline copy with overlapping tasks for one role. CueSheet identifies both tasks and prevents that export. Owen corrects a time and retries successfully without help, then deletes the trial sheet. The source is unchanged. Jo verifies the visible error, recovery, and undo.',
'O06':'On the next Wednesday, Jo watches Owen return without a reminder, produce the correct sheet from a new timeline in 4 minutes, and hand it to the stage volunteers.',
'O07':'Owen explains, “It prints what is on our timeline, so we still have to keep the timeline accurate.” The preview exposes all source fields and makes no claim to detect changes in the live performance schedule beyond those entries.',
'O14':'After week 6, Owen sends Jo an unsolicited note: “I reopen it each Wednesday without reminders. I would miss handing the volunteers a complete sheet without copying the times again.” The communication audit records no builder messages, posts, or reminders after the initial invitation.'},aliases=[],allowed=[] ))

keypath=BASE/'key.json'
key=json.loads(keypath.read_text())
for s in S:
    d=BASE/s['fid'];d.mkdir(exist_ok=True)
    banner='**FICTIONAL evaluation dossier. All people, events, logs, quotes, and tools are invented.**\n\n'
    (d/'README.md').write_text('# '+s['tool']+'\n\n'+banner+s['readme']+'\n')
    (d/'pitch.md').write_text('# Builder pitch\n\n'+banner+s['pitch']+'\n')
    session='# First session and observation record\n\n'+banner+'This is a scripted scenario, not a real user study. Independent participants are outside the builder team. A builder is present only where a record explicitly says so.\n\n'
    session+='\n\n'.join('['+oid+'] '+text for oid,text in s['observations'].items())+'\n'
    (d/'first_session.md').write_text(stamp_session(session, s['fid']))
    prompted=s['trap']=='prompted_return'
    rows=[]
    for week,opens in enumerate(s['counts'],1):
        initial=1 if week==1 else 0
        rows.append({'scenario':'FICTIONAL','observation_id':f'O{week+7:02d}','week':week,'user':s['person'],'weekly_opens':opens,'initial_invited_opens':initial,'prompted_opens':opens-initial if prompted else 0,'unprompted_opens':0 if prompted else opens-initial,'builder_posts':1 if prompted and week in [1,3,5] else 0,'builder_reminders':0,'opens_within_post_window':opens if prompted else 0,'post_window_hours':2 if prompted else 0,'source':'fictional per-user event log and communication audit'})
    rows = stamp_usage(rows)
    with (d/'usage.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
    meta={'schema_version':1,'fictional':True,'fixture_id':s['fid'],'tool_name':s['tool'],'named_user':s['person'],'user_role':s['role'],'setting':s['setting'],'job':s['job'],'baseline_cost':s['cost'],'files':['README.md','pitch.md','first_session.md','usage.csv'],'evidence_boundary':'All events are fictional. Treat the scenario records as the entire dossier. No facts outside the supplied records may be invented.'}
    meta['fictional_calendar'] = calendar_for(s['fid'])
    (d/'dossier.json').write_text(json.dumps(meta,indent=2)+'\n')
    obs={}
    for oid,text in s['observations'].items():
        cs=[c for c,v in s['levels'].items() if oid in v[2]]
        ceiling=REPEATED if oid=='O14' and not prompted else SEEN
        obs[oid]={'kind':'specific_user_report' if oid=='O14' else 'outside_user_observation','external_user':s['person'],'criteria':cs,'rating_support':{c:s['levels'][c][0] for c in cs},'evidence_ceiling':ceiling,'text':text}
    for row in rows:
        obs[row['observation_id']]={'kind':'usage_log','external_user':s['person'],'criteria':['Return'],'rating_support':{'Return':s['levels']['Return'][0]},'evidence_ceiling':SEEN if prompted else REPEATED,'text':json.dumps(row)}
    ready=all(s['levels'][c][0]=='Solid' and s['levels'][c][1] in [SEEN,REPEATED] for c in CRITERIA[:5])
    zone='worth_using' if ready and s['levels']['Return'][0]=='Solid' and s['levels']['Return'][1]==REPEATED else 'stranger_ready' if ready else 'not_ready'
    reasons={c:('; '.join(obs[oid]['text'] for oid in v[2][:2])) for c,v in s['levels'].items()}
    # Preserve finalized oracle refinements and team expectations on an explicit reauthoring pass.
    key['fixtures'].setdefault(s['fid'], {'fictional':True,'main_trap':s['trap'],'named_user':s['person'],'job':s['job'],'criteria':{c:{'rating':v[0],'evidence':v[1],'observation_ids':v[2],'reason':reasons[c]} for c,v in s['levels'].items()},'zone':zone,'observations':obs,'trap_aliases':s['aliases'],'allowed_problem_claims':s['allowed'],'disallowed_evidence_sources':['builder pitch alone','agent confidence','unspecified outside users','hypothetical future tests'],'return_check':{'who':s['person'],'when':'the next normal weekly job after week 6','counts_as_return':'opens and completes the ordinary job without an invitation, reminder, or promotional post'}})
key['fixtures']=dict(sorted(key['fixtures'].items()))
key['suite_fixture_ids']=list(key['fixtures'])
key['suite_construction']='Offline authoring after a two-fixture, one-seed canned-transport pilot. Live model pilot is still required before empirical full runs.'
keypath.write_text(json.dumps(key,indent=2)+'\n')
print('Created 10 remaining fictional fixtures; 12 total. No model results generated.')
