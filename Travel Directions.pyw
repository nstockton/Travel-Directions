# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import calendar
from datetime import datetime
import os.path
import platform
import sys
from threading import Thread

from bs4 import BeautifulSoup
import dateutil.tz
import googlemaps
from googlemaps.exceptions import ApiError, HTTPError, Timeout, TransportError
import requests.packages.urllib3
import wx
import wx.lib.dialogs
try:
	# WXPython Phoenix.
	from wx.adv import Sound, SOUND_ASYNC
except ImportError:
	from wx import Sound, SOUND_ASYNC
try:
	from speechlight import Speech
except ImportError:
	Speech = None

from constants import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, ABOUT_TEXT

try:
	from key import API_KEY
except ImportError:
	API_KEY = None

try:
	if sys.frozen or sys.importers:
		CURRENT_DIRECTORY = os.path.dirname(sys.executable)
		os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(CURRENT_DIRECTORY, "cacert.pem")
except AttributeError:
	CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

try:
	MULTIPLE_CHOICE_SOUND = os.path.join(CURRENT_DIRECTORY, "sounds/multiple_choice.wav")
	with open(MULTIPLE_CHOICE_SOUND, "rb"):
		pass
except IOError:
	MULTIPLE_CHOICE_SOUND = None

SYSTEM_PLATFORM = platform.system()
if SYSTEM_PLATFORM == "Darwin":
	from Cocoa import NSSound

HTML_PARSER = "html.parser"

try:
	xrange
except NameError:
	# Python 3 compatibility.
	xrange = range


class MainFrame(wx.Frame):
	def __init__(self, *args, **kwargs):
		wx.Frame.__init__(self, *args, **kwargs)
		menu_bind = lambda item, handler: self.Bind(wx.EVT_MENU, handler, item)
		self.menu_bar = wx.MenuBar()
		self.SetMenuBar(self.menu_bar)
		self.menu_file = wx.Menu()
		self.menu_help = wx.Menu()
		self.menu_bar.Append(self.menu_file, "&File")
		menu_bind(self.menu_file.Append(wx.ID_ANY, "E&xit"), self.on_exit)
		self.menu_bar.Append(self.menu_help, "&Help")
		menu_bind(self.menu_help.Append(wx.ID_ANY, "&About {}".format(APP_NAME)), self.on_about)
		self.panel = wx.Panel(self, wx.ID_ANY)
		self.panel.SetBackgroundColour("MEDIUM FOREST GREEN")
		self.panel.SetForegroundColour("White")
		self.label_origin_area = wx.StaticText(self.panel, wx.ID_ANY, "&Start From:")
		self.origin_area = wx.TextCtrl(self.panel, wx.ID_ANY, style=wx.TE_NOHIDESEL)
		self.label_destination_area = wx.StaticText(self.panel, wx.ID_ANY, "&Destination:")
		self.destination_area = wx.TextCtrl(self.panel, wx.ID_ANY, style=wx.TE_NOHIDESEL)
		self.label_modes = wx.StaticText(self.panel, wx.ID_ANY, "Travel &Mode:")
		self.modes = wx.Choice(self.panel, wx.ID_ANY, choices=["Driving", "Walking", "Bicycling", "Transit"])
		self.modes.Bind(wx.EVT_CHOICE, self.on_mode_changed, self.modes)
		self.modes.SetSelection(0)
		self.label_waypoints_area = wx.StaticText(self.panel, wx.ID_ANY, "&Waypoints:")
		self.waypoints_area = wx.TextCtrl(self.panel, wx.ID_ANY, style=wx.TE_NOHIDESEL)
		self.optimize_waypoints = wx.CheckBox(self.panel, wx.ID_ANY, label="Optimi&ze Waypoints", style=wx.CHK_2STATE | wx.ALIGN_RIGHT)
		self.avoid_highways = wx.CheckBox(self.panel, wx.ID_ANY, label="Avoid H&ighways", style=wx.CHK_2STATE | wx.ALIGN_RIGHT)
		self.avoid_tolls = wx.CheckBox(self.panel, wx.ID_ANY, label="Avoid &Toll Roads", style=wx.CHK_2STATE | wx.ALIGN_RIGHT)
		self.avoid_ferries = wx.CheckBox(self.panel, wx.ID_ANY, label="Avoid F&erries", style=wx.CHK_2STATE | wx.ALIGN_RIGHT)
		self.label_depart_arrive = wx.StaticText(self.panel, wx.ID_ANY, "Type:")
		self.depart_arrive = wx.Choice(self.panel, wx.ID_ANY, choices=["Depart after", "Arrive By"])
		self.label_depart_arrive.Disable()
		self.depart_arrive.Disable()
		self.label_months = wx.StaticText(self.panel, wx.ID_ANY, "Date:")
		self.months = wx.Choice(self.panel, wx.ID_ANY, choices=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
		self.months.Bind(wx.EVT_CHOICE, self.on_date_changed, self.months)
		self.label_months.Disable()
		self.months.Disable()
		self.label_days = wx.StaticText(self.panel, wx.ID_ANY, "/")
		self.days = wx.Choice(self.panel, wx.ID_ANY, choices=[], style=wx.WANTS_CHARS)
		self.days.Bind(wx.EVT_CHOICE, self.on_date_changed, self.days)
		self.days.Bind(wx.EVT_KEY_DOWN, self.on_date_key_press)
		self.days.SetInitialSize((40, 20))
		self.label_days.Disable()
		self.days.Disable()
		self.label_years = wx.StaticText(self.panel, wx.ID_ANY, "/")
		self.years = wx.TextCtrl(self.panel, wx.ID_ANY, style=wx.TE_READONLY | wx.TE_NOHIDESEL)
		self.years.SetInitialSize((50, 20))
		self.label_years.Disable()
		self.years.Disable()
		self.label_hours = wx.StaticText(self.panel, wx.ID_ANY, "At:")
		self.hours = wx.Choice(self.panel, wx.ID_ANY, choices=[str(x) for x in xrange(1, 13)], style=wx.WANTS_CHARS)
		self.hours.Bind(wx.EVT_CHOICE, self.on_date_changed, self.hours)
		self.hours.Bind(wx.EVT_KEY_DOWN, self.on_date_key_press)
		self.label_hours.Disable()
		self.hours.Disable()
		self.label_minutes = wx.StaticText(self.panel, wx.ID_ANY, ":")
		self.minutes = wx.Choice(self.panel, wx.ID_ANY, choices=["{:02d}".format(x) for x in xrange(60)])
		self.minutes.Bind(wx.EVT_CHOICE, self.on_date_changed, self.minutes)
		self.label_minutes.Disable()
		self.minutes.Disable()
		self.label_am_pm = wx.StaticText(self.panel, wx.ID_ANY, " ")
		self.am_pm = wx.Choice(self.panel, wx.ID_ANY, choices=["A.M.", "P.M."])
		self.am_pm.Bind(wx.EVT_CHOICE, self.on_date_changed, self.am_pm)
		self.label_am_pm.Disable()
		self.am_pm.Disable()
		self.label_transit_mode = wx.StaticText(self.panel, wx.ID_ANY, "Travel By:")
		self.transit_mode = wx.Choice(self.panel, wx.ID_ANY, choices=["Bus And Rail", "Bus Only", "Rail Only"])
		self.label_transit_mode.Disable()
		self.transit_mode.Disable()
		self.label_transit_routing_preference = wx.StaticText(self.panel, wx.ID_ANY, "Routing Preference:")
		self.transit_routing_preference = wx.Choice(self.panel, wx.ID_ANY, choices=["Best", "Less Walking", "Fewer Transfers"])
		self.label_transit_routing_preference.Disable()
		self.transit_routing_preference.Disable()
		self.plan_button = wx.Button(self.panel, label = "&Plan Trip")
		self.plan_button.Bind(wx.EVT_BUTTON, self.on_search)
		self.label_routes = wx.StaticText(self.panel, wx.ID_ANY, "&Route Selection:")
		self.routes = wx.Choice(self.panel, wx.ID_ANY, choices=[])
		self.routes.Bind(wx.EVT_CHOICE, self.on_route_changed, self.routes)
		self.label_routes.Disable()
		self.routes.Disable()
		self.label_output_area = wx.StaticText(self.panel, wx.ID_ANY, "Result &Details:")
		self.output_area = wx.TextCtrl(self.panel, wx.ID_ANY, style = wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NOHIDESEL)
		self.output_area.SetBackgroundColour("Black")
		self.output_area.SetForegroundColour("White")
		self.output_area.Disable()
		self.status_bar = wx.StatusBar(self.panel)
		self.origin_sizer = wx.BoxSizer()
		self.origin_sizer.Add(self.label_origin_area)
		self.origin_sizer.Add(self.origin_area, proportion=1, border=1)
		self.destination_sizer = wx.BoxSizer()
		self.destination_sizer.Add(self.label_destination_area)
		self.destination_sizer.Add(self.destination_area, proportion=1, border=1)
		self.waypoints_sizer = wx.BoxSizer()
		self.waypoints_sizer.Add(self.label_waypoints_area)
		self.waypoints_sizer.Add(self.waypoints_area, proportion=1, border=1)
		self.non_transit_sizer = wx.BoxSizer()
		self.non_transit_sizer.Add(self.optimize_waypoints, proportion=0, border=1)
		self.non_transit_sizer.Add(self.avoid_highways, proportion=0, border=1)
		self.non_transit_sizer.Add(self.avoid_tolls, proportion=0, border=1)
		self.non_transit_sizer.Add(self.avoid_ferries, proportion=0, border=1)
		self.modes_sizer = wx.BoxSizer()
		self.modes_sizer.Add(self.label_modes)
		self.modes_sizer.Add(self.modes, proportion=0, flag=wx.EXPAND, border=0)
		self.depart_arrive_sizer = wx.BoxSizer()
		self.depart_arrive_sizer.Add(self.label_depart_arrive)
		self.depart_arrive_sizer.Add(self.depart_arrive, proportion=0, flag=wx.EXPAND, border=0)
		self.date_time_sizer = wx.BoxSizer()
		self.date_time_sizer.Add(self.label_months)
		self.date_time_sizer.Add(self.months, proportion=0, flag=wx.EXPAND, border=0)
		self.date_time_sizer.Add(self.label_days)
		self.date_time_sizer.Add(self.days, proportion=0, flag=wx.EXPAND, border=0)
		self.date_time_sizer.Add(self.label_years)
		self.date_time_sizer.Add(self.years, proportion=0, flag=wx.EXPAND, border=0)
		self.date_time_sizer.Add(self.label_hours)
		self.date_time_sizer.Add(self.hours, proportion=0, flag=wx.EXPAND, border=0)
		self.date_time_sizer.Add(self.label_minutes)
		self.date_time_sizer.Add(self.minutes, proportion=0, flag=wx.EXPAND, border=0)
		self.date_time_sizer.Add(self.label_am_pm)
		self.date_time_sizer.Add(self.am_pm, proportion=0, flag=wx.EXPAND, border=0)
		self.transit_preferences_sizer = wx.BoxSizer()
		self.transit_preferences_sizer.Add(self.label_transit_mode)
		self.transit_preferences_sizer.Add(self.transit_mode, proportion=0, flag=wx.EXPAND, border=0)
		self.transit_preferences_sizer.Add(self.label_transit_routing_preference)
		self.transit_preferences_sizer.Add(self.transit_routing_preference, proportion=0, flag=wx.EXPAND, border=0)
		self.routes_sizer = wx.BoxSizer()
		self.routes_sizer.Add(self.label_routes)
		self.routes_sizer.Add(self.routes, proportion=1, flag=wx.EXPAND, border=1)
		self.status_bar_sizer = wx.BoxSizer()
		self.status_bar_sizer.Add(self.status_bar, proportion=1, border=0)
		self.entry_sizer = wx.BoxSizer(wx.VERTICAL)
		self.entry_sizer.Add(self.origin_sizer, proportion=0, flag=wx.EXPAND | wx.TOP, border=150)
		self.entry_sizer.Add(self.destination_sizer, proportion=0, flag=wx.EXPAND | wx.TOP, border=1)
		self.entry_sizer.Add(self.modes_sizer, proportion=0, flag=wx.EXPAND | wx.TOP, border=15)
		self.entry_sizer.Add(self.waypoints_sizer, proportion=0, flag=wx.EXPAND | wx.TOP, border=25)
		self.entry_sizer.Add(self.non_transit_sizer, proportion=0, flag=wx.EXPAND | wx.TOP, border=5)
		self.entry_sizer.Add(self.depart_arrive_sizer, proportion=0, flag=wx.EXPAND | wx.TOP, border=25)
		self.entry_sizer.Add(self.date_time_sizer, proportion=0, flag=wx.EXPAND | wx.TOP, border=10)
		self.entry_sizer.Add(self.transit_preferences_sizer, proportion=0, flag=wx.EXPAND | wx.TOP, border=10)
		self.entry_sizer.Add(self.plan_button, proportion=0, flag=wx.EXPAND | wx.TOP | wx.ALIGN_CENTER_HORIZONTAL, border=30)
		self.results_sizer = wx.BoxSizer(wx.VERTICAL)
		self.results_sizer.Add(self.routes_sizer, proportion=0, flag=wx.EXPAND, border=1)
		self.results_sizer.Add(self.label_output_area)
		self.results_sizer.Add(self.output_area, proportion=1, flag=wx.EXPAND, border=0)
		self.horizontal_sizer = wx.BoxSizer()
		self.horizontal_sizer.Add(self.entry_sizer, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=25)
		self.horizontal_sizer.Add(self.results_sizer, proportion=2, flag=wx.EXPAND, border=0)
		self.main_sizer = wx.BoxSizer(wx.VERTICAL)
		self.main_sizer.Add(self.horizontal_sizer, proportion=10, flag=wx.EXPAND, border=1)
		self.main_sizer.Add(self.status_bar_sizer, proportion=1, flag=wx.EXPAND, border=0)
		self.panel.SetSizer(self.main_sizer)
		self.Show()
		self.status_bar.SetStatusText(" ")
		rkwargs = {}
		if API_KEY is not None and isinstance(API_KEY, str) and API_KEY.strip():
			self.gmaps = googlemaps.Client(key=API_KEY, timeout=20, requests_kwargs=rkwargs)
		else:
			self.notify("error", "API key not found. See the ReadMe for instructions on how to obtain one.")
			return self.Destroy()
		if Speech is not None:
			self.speech = Speech()
			self.say = self.speech.say
		else:
			self.say = lambda *args, **kwargs: None
		self.tz_utc = dateutil.tz.tzutc()
		self.tz_local = dateutil.tz.tzlocal()
		self.results = []

	def notify(self, msg_type, msg_text, msg_title=""):
		"""Display a notification to the user."""
		if not msg_title:
			msg_title = msg_type.capitalize()
		if msg_type == "question":
			notify_box = wx.MessageDialog(self, message=msg_text, caption=msg_title, style=wx.ICON_QUESTION | wx.YES_NO)
			modal = notify_box.ShowModal()
			notify_box.Destroy()
			return modal == wx.ID_YES
		elif msg_type == "error":
			notify_box = wx.MessageDialog(self, message=msg_text, caption=msg_title, style=wx.ICON_ERROR | wx.OK)
		elif msg_type == "information":
			notify_box = wx.MessageDialog(self, message=msg_text, caption=msg_title, style=wx.ICON_INFORMATION | wx.OK)
		elif msg_type == "scrolled":
			notify_box = wx.lib.dialogs.ScrolledMessageDialog(self, msg_text, msg_title)
		if notify_box.ShowModal() == wx.ID_OK:
			notify_box.Destroy()

	def play_sound(self, filename=None):
		if not filename:
			return
		elif SYSTEM_PLATFORM == "Darwin":
			# Use Cocoa for playing sounds on Mac.
			sound = NSSound.alloc()
			sound.initWithContentsOfFile_byReference_(filename, True)
			sound.play()
		else:
			try:
				snd = Sound()
				if snd.Create(filename):
					snd.Play(SOUND_ASYNC)
			except NotImplementedError:
				# Sound support not implemented on this platform.
				pass

	def on_about(self, event):
		"""Displays the about dialog."""
		self.notify("scrolled", ABOUT_TEXT, "About {}".format(APP_NAME))

	def on_exit(self, event):
		"""Exits the program."""
		self.Destroy()

	def selected_datetime(self):
		"""Returns a datetime object with the currently selected values on the GUI"""
		year = int(self.years.GetValue())
		month = self.months.GetSelection() + 1
		day = self.days.GetSelection() + 1
		hour = ((self.hours.GetSelection() + 1) % 12) + 12 if self.am_pm.GetSelection() == 1 else 0
		minute = self.minutes.GetSelection()
		return datetime(year, month, day, hour, minute)

	def on_date_changed(self, event):
		event_object = event.GetEventObject()
		if event_object is self.months:
			# If a new month has been selected, reset the day to the 1st of the month.
			# If this is not done before a datetime object for the selected date is built, a day value outside of the valid range for the newly selected month could be passed to the datetime constructor, resulting in an exception being thrown.
			self.days.SetSelection(0)
		now = datetime.now()
		selected = self.selected_datetime()
		# If the month, day, or hour selected by the user is in the present or future, use the current year. Otherwise, use the year following current.
		year = now.year if (selected.month, selected.day, selected.hour) >= (now.month, now.day, now.hour) else now.year + 1
		self.years.SetValue("{}".format(year))
		if event_object is self.months:
			month = event.GetSelection() + 1
			max_days = calendar.monthrange(year, month)[1]
			self.days.SetItems(["{:02d}".format(x) for x in xrange(1, max_days + 1)])
			self.days.SetSelection(0)

	def on_date_key_press(self, event):
		event_object = event.GetEventObject()
		key_code = event.GetKeyCode()
		modifiers = event.GetModifiers()
		if not modifiers and key_code in (wx.WXK_TAB, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			if event_object is self.days:
				self.years.SetFocus()
			elif event_object is self.hours:
				self.minutes.SetFocus()
		elif modifiers == wx.MOD_SHIFT and key_code == wx.WXK_TAB:
			if event_object is self.days:
				self.months.SetFocus()
			elif event_object is self.hours:
				self.years.SetFocus()
		else:
			event.Skip()

	def on_mode_changed(self, event):
		if self.modes.GetString(self.modes.GetSelection()) == "Transit":
			self.label_waypoints_area.Disable()
			self.waypoints_area.Disable()
			self.optimize_waypoints.Disable()
			self.avoid_highways.Disable()
			self.avoid_tolls.Disable()
			self.avoid_ferries.Disable()
			now = datetime.now()
			self.depart_arrive.SetSelection(0)
			self.label_depart_arrive.Enable()
			self.depart_arrive.Enable()
			self.years.SetValue("{}".format(now.year))
			self.label_years.Enable()
			self.years.Enable()
			self.months.SetSelection(now.month - 1)
			self.label_months.Enable()
			self.months.Enable()
			max_days = calendar.monthrange(now.year, now.month)[1]
			self.days.SetItems(["{:02d}".format(x) for x in xrange(1, max_days + 1)])
			self.days.SetSelection(now.day - 1)
			self.label_days.Enable()
			self.days.Enable()
			hour = now.hour
			if hour < 12:
				if hour == 0:
					hour = 12
				self.am_pm.SetSelection(0)
			else:
				if hour > 12:
					hour -= 12
				self.am_pm.SetSelection(1)
			self.hours.SetSelection(hour - 1)
			self.label_hours.Enable()
			self.hours.Enable()
			self.minutes.SetSelection(now.minute)
			self.label_minutes.Enable()
			self.minutes.Enable()
			self.label_am_pm.Enable()
			self.am_pm.Enable()
			self.transit_mode.SetSelection(0)
			self.label_transit_mode.Enable()
			self.transit_mode.Enable()
			self.transit_routing_preference.SetSelection(0)
			self.label_transit_routing_preference.Enable()
			self.transit_routing_preference.Enable()
		else:
			self.label_waypoints_area.Enable()
			self.waypoints_area.Enable()
			self.optimize_waypoints.Enable()
			self.avoid_highways.Enable()
			self.avoid_tolls.Enable()
			self.avoid_ferries.Enable()
			self.label_depart_arrive.Disable()
			self.depart_arrive.Disable()
			self.label_months.Disable()
			self.months.Disable()
			self.label_days.Disable()
			self.days.Disable()
			self.label_years.Disable()
			self.years.Disable()
			self.label_hours.Disable()
			self.hours.Disable()
			self.label_minutes.Disable()
			self.minutes.Disable()
			self.label_am_pm.Disable()
			self.am_pm.Disable()
			self.label_transit_mode.Disable()
			self.transit_mode.Disable()
			self.label_transit_routing_preference.Disable()
			self.transit_routing_preference.Disable()

	def on_route_changed(self, event):
		"""Update the details box when the selection is changed."""
		i = event.GetSelection()
		self.output_area.SetValue(self.results[i])

	def on_search(self, event):
		"""Performs a directions search."""
		del self.results[:]
		self.label_routes.Disable()
		self.routes.Disable()
		self.routes.Clear()
		self.label_output_area.Disable()
		self.output_area.Disable()
		self.output_area.Clear()
		origin = self.origin_area.GetValue().strip()
		destination = self.destination_area.GetValue().strip()
		if not origin or not destination:
			return self.notify("error", "You must supply a starting location and a destination.")
		mode = self.modes.GetString(self.modes.GetSelection()).lower()
		waypoints = [point.strip() for point in self.waypoints_area.GetValue().split("|")]
		if waypoints:
			optimize_waypoints = self.optimize_waypoints.IsChecked()
		avoid = []
		if self.avoid_highways.IsChecked():
			avoid.append("highways")
		if self.avoid_tolls.IsChecked():
			avoid.append("tolls")
		if self.avoid_ferries.IsChecked():
			avoid.append("ferries")
		self.origin_area.Clear()
		self.destination_area.Clear()
		self.waypoints_area.Clear()
		self.optimize_waypoints.SetValue(False)
		self.avoid_highways.SetValue(False)
		self.avoid_tolls.SetValue(False)
		self.avoid_ferries.SetValue(False)
		self.say("Planning Trip.", True)
		params = {
			"origin": origin,
			"destination": destination,
			"mode": mode,
			"alternatives": True,
			"language": "en",
			"region": "us",
			"units": "imperial" # can also be "metric".
		}
		if mode == "transit":
			depart_arrive = ("departure_time", "arrival_time")[self.depart_arrive.GetSelection()]
			dt = self.selected_datetime().replace(tzinfo=self.tz_local).astimezone(self.tz_utc)
			params[depart_arrive] = calendar.timegm(dt.utctimetuple())
			if self.transit_mode.GetSelection():
				params["transit_mode"] = ("bus", "rail")[self.transit_mode.GetSelection() - 1]
			if self.transit_routing_preference.GetSelection():
				params["transit_routing_preference"] = ("less_walking", "fewer_transfers")[self.transit_routing_preference.GetSelection() - 1]
		else:
			if waypoints:
				params["waypoints"] = waypoints
				params["optimize_waypoints"] = optimize_waypoints
			if avoid:
				params["avoid"] = avoid
		self.modes.SetSelection(0)
		self.on_mode_changed(event.GetEventObject())
		t = Thread(target=self._retrieve, kwargs=params)
		t.start()

	def _retrieve(self, **params):
		try:
			response = self.gmaps.directions(**params)
		except Timeout:
			return self.notify("error", "The server failed to respond.")
		except (ApiError, HTTPError, TransportError) as e:
			return self.notify("error", e.message)
		wx.CallAfter(self._process_results, response)

	def _process_results(self, response):
		summaries = []
		text = []
		for route_counter, route in enumerate(response):
			summaries.append("Route {}".format(route_counter + 1))
			details = []
			for leg in route["legs"]:
				details.append("From: {}\nTo: {}".format(leg["start_address"], leg["end_address"]))
				if "distance" in leg:
					text.append("Total Distance: {}".format(leg["distance"]["text"]))
				if "duration" in leg:
					text.append("({})".format(leg["duration"]["text"]))
				if text:
					details.append(" ".join(text))
					del text[:]
				if "departure_time" in leg:
					details.append("Departing: {}".format(leg["departure_time"]["text"]))
				if "arrival_time" in leg:
					details.append("Arriving: {}".format(leg["arrival_time"]["text"]))
				for step in leg["steps"]:
					transit_details = step["transit_details"] if "transit_details" in step else {}
					line = transit_details["line"] if "line" in transit_details else {}
					vehicle = line["vehicle"] if "vehicle" in line else {}
					if "departure_time" in transit_details:
						text.append("At {},".format(transit_details["departure_time"]["text"]))
					if "short_name" in line or "name" in line:
						text.append("board")
					if "short_name" in line:
						text.append(line["short_name"])
					if "name" in line:
						text.append(line["name"])
					if "name" in vehicle:
						text.append(vehicle["name"])
					if "headsign" in transit_details:
						text.append("to {}".format(transit_details["headsign"]))
					if "departure_stop" in transit_details:
						text.append("from {}".format(transit_details["departure_stop"]["name"]))
					if "num_stops" in transit_details:
						text.append("\nTravel {} stops,".format(transit_details["num_stops"]))
					if step["travel_mode"] != "TRANSIT" and "html_instructions" in step:
						text.append("\n".join(BeautifulSoup(step["html_instructions"].replace("<b>", "").replace("</b>", ""), HTML_PARSER).findAll(text=True)))
						details.append(" ".join(text).capitalize())
						del text[:]
					if "distance" in step:
						text.append("Travel {}".format(step["distance"]["text"]))
					if "duration" in step:
						text.append("(about {})".format(step["duration"]["text"]))
					if text:
						details.append(" ".join(text).capitalize())
						del text[:]
					if "arrival_time" in transit_details:
						text.append("At {}".format(transit_details["arrival_time"]["text"]))
					if "arrival_stop" in transit_details:
						text.append("disembark at {}".format(transit_details["arrival_stop"]["name"]))
					if text:
						details.append(" ".join(text).capitalize())
						del text[:]
					sub_steps = step["steps"] if "steps" in step else []
					for sub_step in sub_steps:
						if "html_instructions" in sub_step:
							details.append("* " + "\n* ".join(BeautifulSoup(sub_step["html_instructions"].replace("<b>", "").replace("</b>", ""), HTML_PARSER).findAll(text=True)).capitalize())
							if "distance" in sub_step:
								text.append("Travel {}".format(sub_step["distance"]["text"]))
							if "duration" in sub_step:
								text.append("(about {})".format(sub_step["duration"]["text"]))
							if text:
								details.append("* " + " ".join(text).capitalize())
								del text[:]
			if "warnings" in route:
				details.append("")
				details.append("\n".join(route["warnings"]))
			self.results.append("\n".join(details).strip())
		self.say("{} Route{} found.".format(len(self.results), "" if len(self.results) == 1 else "s"))
		if not self.results:
			return
		self.routes.SetItems(summaries)
		self.routes.SetSelection(0)
		self.output_area.SetValue(self.results[0])
		self.label_output_area.Enable()
		self.output_area.Enable()
		if len(self.results) > 1:
			self.label_routes.Enable()
			self.routes.Enable()
			if MULTIPLE_CHOICE_SOUND:
				self.play_sound(MULTIPLE_CHOICE_SOUND)
			self.routes.SetFocus()
		else:
			self.output_area.SetFocus()


app = wx.App(redirect=False)
window = MainFrame(None, title=APP_NAME, size=(WINDOW_WIDTH, WINDOW_HEIGHT))
app.SetTopWindow(window)
window.Center()
window.ShowFullScreen(True,wx.FULLSCREEN_NOTOOLBAR)
app.MainLoop()
