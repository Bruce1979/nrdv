#!/usr/local/bin/python3
import wx, wx.html
import os, json

class MainFrame(wx.Frame):

  def __init__(self, *args, **kwargs):
    super(MainFrame, self).__init__(*args, **kwargs)

    self.sides = ['Corporations', 'Runners']

    self.factions = {
      'Corporations': ['haas-bioroid','jinteki','nbn','weyland-consortium'],
      'Runners': ['anarch','criminal','shaper','apex','adam','sunny-lebeau'],
    }

    self.combinations = {
      'Corporations': None,
      'Runners': None,
    }

    # load data from files
    cards_file = 'cards.json'
    decks_file = 'decks.json'
    valid_corp_file = 'valid_corp_combinations.json'
    valid_runner_file = 'valid_runner_combinations.json'

    with open(decks_file) as f:
      self.decks = json.load(f)

    with open(cards_file) as f:
      self.cards = json.load(f)

    with open(valid_corp_file) as f:
      self.combinations['Corporations'] = json.load(f)

    with open(valid_runner_file) as f:
      self.combinations['Runners'] = json.load(f)

    # state tracking
    self.current_side = None

    # build UI
    self.InitUI()

  def InitUI(self):

    # widget default values
    self.default_blank_choices = list(['-- Choose one ---'])

    # menubar and options
    menu_bar = wx.MenuBar()
    help_menu = wx.Menu()
    help_menu.Append(wx.ID_ABOUT, "About NRDeckViewer")
    help_menu.Append(wx.ID_HELP, "NRDeckViewer Help", "Help documentation for NRDeckViewer")
    menu_bar.Append(help_menu, "Help")
    self.SetMenuBar(menu_bar)
    self.Bind(wx.EVT_MENU, self.on_about_request, id=wx.ID_ABOUT)
    self.Bind(wx.EVT_MENU, self.on_help_request, id=wx.ID_HELP)

    # status bar
    status_bar = wx.StatusBar(self)
    self.SetStatusBar(status_bar)

    # window contents
    # main panel
    main_panel = wx.Panel(self)
    main_sizer = wx.BoxSizer(wx.VERTICAL)

    # top panel
    top_panel = wx.Panel(main_panel)
    top_sizer = wx.BoxSizer(wx.HORIZONTAL)
    side_selector = wx.Choice(top_panel, choices=self.default_blank_choices + self.sides)
    self.Bind(wx.EVT_CHOICE, self.select_side, id=side_selector.GetId())
    top_sizer.Add(side_selector, 0, wx.EXPAND | wx.ALL, 0)
    top_panel.SetSizer(top_sizer)

    # bottom panel
    bottom_panel = wx.Panel(main_panel)
    bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
    bottom_panel.SetSizer(bottom_sizer)

    main_sizer.Add(top_panel, 0, wx.EXPAND | wx.ALL, 0)
    main_sizer.Add(bottom_panel, 0, wx.EXPAND | wx.ALL, 0)

    main_panel.SetSizerAndFit(main_sizer)

    # App layout
    self.SetAutoLayout(True)
    self.SetTitle('Netrunner Deck Viewer')
    self.Centre()
    self.Layout()

  def split_combos_by_faction(self,combos):
    factions = {}
    for deck in combos[0].split(','):
      factions[self.decks[deck]['faction_code']] = set()
    for combo in combos:
      for deck in combo.split(','):
        factions[self.decks[deck]['faction_code']].add(deck)
    return factions

  def show_faction_deck(self, e):
    print(e.GetString())
    for sizer in self.bottom_sizer:
      print(sizer)

  def select_side(self,e):
    chosen_side = e.GetString()
    bottom_panel = self.GetChildren()[1].GetChildren()[1]
    bottom_sizer = bottom_panel.GetSizer()
    if chosen_side not in self.default_blank_choices and chosen_side != self.current_side:
      self.current_side = chosen_side
      for child in bottom_panel.GetChildren():
        child.Destroy()
      combos = sorted([key for key in self.combinations[chosen_side]['valid']])
      factions = self.split_combos_by_faction(combos)
      for faction in factions:
        faction_panel = wx.Panel(bottom_panel)
        faction_sizer = wx.BoxSizer(wx.VERTICAL)
        faction_name = wx.StaticText(faction_panel, label=faction)
        faction_choices = self.default_blank_choices+list(factions[faction])
        faction_chooser = wx.Choice(faction_panel, choices=faction_choices)
        self.Bind(wx.EVT_CHOICE, self.show_faction_deck, id=faction_chooser.GetId())
        faction_panel.SetSizer(faction_sizer)
        bottom_sizer.Add(faction_panel, 0, wx.EXPAND | wx.ALL, 0)
      print(bottom_panel.GetChildren())
      print(bottom_sizer.GetChildren())
      self.Fit()
      self.Layout()


  def select_deck(self,e):
    print(e.GetSelection())

  def on_open_request(self,e):
    cwd = os.getcwd()
    dlg = wx.FileDialog(self, "Choose a file", cwd, "", "*.*", wx.FLP_OPEN)
    if dlg.ShowModal() == wx.ID_OK:
      filename=dlg.GetFilename()
      dirname=dlg.GetDirectory()
      filehandle=open(os.path.join(dirname, filename),'r')
      # Load file into var
      file_contents = filehandle.read()
      filehandle.close()
    dlg.Destroy()

  def on_about_request(self,e):
    msg = "This is the about text\n\nA second line."
    dlg = wx.MessageDialog(None,msg,"About NRDeckViewer",wx.OK)
    dlg.ShowModal()
    dlg.Destroy()

  def on_help_request(self,e):
    help_window = wx.html.HtmlHelpController()
    help_window.AddBook('help/help.hhp')
    help_window.SetTitleFormat('NRDeckViewer Help')
    help_window.DisplayContents()
    help_window.Display()   # Throws error, but without doesn't display(?)

def main():

  app = wx.App()
  main_frame = MainFrame(None)
  main_frame.Show()
  app.MainLoop()


if __name__ == '__main__':
  main()
