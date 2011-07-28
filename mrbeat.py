#!/usr/bin/python

import pygtk
import gtk
import gtk.glade
import time
import pygame.mixer
import logging

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(name)-10s %(levelname)-8s %(message)s",
                    datefmt='%H:%M:%S',
                    handlers= logging.StreamHandler())
log = logging.getLogger('mrbeat');
log.debug('starting')

#defines
TIMER_ACCURACY = 25
BEAT_LENGTH = 1
FREQ = 44100
BITSIZE = -16
CHANNELS = 2
BUFFER = 1024
FRAMERATE = 30

def mean(nums):
  if len(nums):
    return float( sum(nums) / len(nums))
  else:
    return 0.0

def currentms():
  return round(time.time()*1000)

def ms_to_bpm(ms):
  return round((1000*60) / ms)

def bpm_to_ms(bpm):
  return round(bpm / (1000*60)) # beats/min * min/ms

pygame.init()

class Main:
  def __init__(self):
    #GUI bits and bobs
    self.wTree = gtk.glade.XML("mainwindow.glade", "mainwindow")
    signals = {
      "on_play_clicked" : self.OnPlay,
      "on_stop_clicked" : self.OnStop,
      "on_quit_clicked" : self.OnQuit,
      "on_volume_master_value_changed" : self.OnVolumeMasterChange,
      "on_volume_accent_value_changed" : self.OnVolumeAccentChange,
      "on_volume_quarter_value_changed" : self.OnVolumeQuarterChange,
      "on_volume_eighth_value_changed" : self.OnVolumeEighthChange,
      "on_volume_triplet_value_changed" : self.OnVolumeTripletChange,
      "on_volume_sixteenth_value_changed" : self.OnVolumeSixteenthChange,
      "on_tempo_value_changed" : self.OnTempoChange,
      "on_bpm_value_changed" : self.OnBpmChange,
      "on_ticktype_accent_changed" : self.OnTicktypeAccentChanged,
      "on_ticktype_quarter_changed" : self.OnTicktypeQuarterChanged,
      "on_ticktype_eighth_changed" : self.OnTicktypeEighthChanged,
      "on_ticktype_triplet_changed" : self.OnTicktypeTripletChanged,
      "on_ticktype_sixteenth_changed" : self.OnTicktypeSixteenthChanged,
      "on_tap_tempo_pressed" : self.TapTempo
    }
    
    self.wTree.signal_autoconnect(signals)
    
    #Glade is too stupid to know how to do this
    self.SetComboboxDefaults()
    
    #General definitions
    self.stopped = True
    self.playing = False  #Should ticks be played?
    
    #Set the counter at zero
    self.ResetBeat()
    
    #Initialize the sound system
    
    try:
      pygame.mixer.init(FREQ, BITSIZE, CHANNELS, BUFFER)
    except pygame.error, exc:
      print "Could not initialize the sound system: %s" % exc
      return 1
    
    #Load tick sounds
    self.tick_sound = pygame.mixer.Sound('sounds/click4.wav')
    self.tock_sound = pygame.mixer.Sound('sounds/click3.wav')
    self.pulse_sound = pygame.mixer.Sound('sounds/pulse.wav')
    self.ping_sound = pygame.mixer.Sound('sounds/ping.wav')
    self.cowbell_sound = pygame.mixer.Sound('sounds/cowbell.wav')
    self.claves_sound = pygame.mixer.Sound('sounds/claves.wav')
    self.agogolow_sound = pygame.mixer.Sound('sounds/agogo1.wav')
    self.agogohigh_sound = pygame.mixer.Sound('sounds/agogo2.wav')
    self.coffeecup_sound = pygame.mixer.Sound('sounds/coffeecup.wav')
    self.shaker_sound = pygame.mixer.Sound('sounds/shaker.wav')
    self.one_sound = pygame.mixer.Sound('sounds/one.wav')
    self.two_sound = pygame.mixer.Sound('sounds/two.wav')
    self.three_sound = pygame.mixer.Sound('sounds/three.wav')
    self.four_sound = pygame.mixer.Sound('sounds/four.wav')
    self.five_sound = pygame.mixer.Sound('sounds/five.wav')
    self.six_sound = pygame.mixer.Sound('sounds/six.wav')
    self.seven_sound = pygame.mixer.Sound('sounds/seven.wav')
    self.eight_sound = pygame.mixer.Sound('sounds/eight.wav')
    self.num_sound = pygame.mixer.Sound('sounds/num.wav')
    self.and_sound = pygame.mixer.Sound('sounds/and.wav')
    self.e_sound = pygame.mixer.Sound('sounds/e.wav')
    self.a_sound = pygame.mixer.Sound('sounds/a.wav')
    self.tee_sound = pygame.mixer.Sound('sounds/tee.wav')
    self.ta_sound = pygame.mixer.Sound('sounds/ta.wav')
    self.null_sound = pygame.mixer.Sound('sounds/nothing.wav')
        
        
    self.volume_master = self.wTree.get_widget("volume_master").get_value()
    self.volume_accent = self.wTree.get_widget("volume_accent").get_value()
    self.volume_quarter = self.wTree.get_widget("volume_quarter").get_value()
    self.volume_eighth = self.wTree.get_widget("volume_eighth").get_value()
    self.volume_triplet = self.wTree.get_widget("volume_triplet").get_value()
    self.volume_sixteenth = self.wTree.get_widget("volume_sixteenth").get_value()
    
    self.ticktype_accent = self.wTree.get_widget("ticktype_accent").get_active()
    self.ticktype_quarter = self.wTree.get_widget("ticktype_quarter").get_active()
    self.ticktype_eighth = self.wTree.get_widget("ticktype_eighth").get_active()
    self.ticktype_triplet = self.wTree.get_widget("ticktype_triplet").get_active()
    self.ticktype_sixteenth = self.wTree.get_widget("ticktype_sixteenth").get_active_text()
    
    #Other vars
    self.tempo = self.wTree.get_widget("tempo").get_value()
    self.bpm = self.wTree.get_widget("bpm").get_value()
    self.taptempo_ticks = 1
    self.taptempo_mode = False
    self.clock = pygame.time.Clock()
    self.last_time = 0.0
    self.last_tap = None
    self.last_beat = 0
    
    #Show the main window
    
    self.window = self.wTree.get_widget("mainwindow")
    self.window.connect("destroy", self.OnQuit)
    self.window.show_all()

  def OnPlay(self, widget):
    if not self.playing:
      self.playing = True
      self.ResetBeat()
      self.ticking_loop()
      
  def OnStop(self, widget):
    self.playing = False
    self.SetBeatLabel('-')
    self.ticks = 0
    self.eighth_ticked = False
    self.sixteenth_ticked = False
    
  def OnQuit(self, widget):
    self.playing = False
    gtk.main_quit()

  def OnVolumeMasterChange(self, widget):
    self.volume_master = widget.get_value()

  def OnVolumeAccentChange(self, widget):
    self.volume_accent = widget.get_value()

  def OnVolumeQuarterChange(self, widget):
    self.volume_quarter = widget.get_value()

  def OnVolumeEighthChange(self, widget):
    self.volume_eighth = widget.get_value()

  def OnVolumeTripletChange(self, widget):
    self.volume_triplet = widget.get_value()

  def OnVolumeSixteenthChange(self, widget):
    self.volume_sixteenth = widget.get_value()

  def OnTempoChange(self, widget):
    self.tempo = widget.get_value()

  def OnBpmChange(self, widget):
    self.bpm = widget.get_value()

  def OnTicktypeAccentChanged(self, widget):
    self.ticktype_accent = widget.get_active()
    #print widget.get_active()

  def OnTicktypeQuarterChanged(self, widget):
    self.ticktype_quarter = widget.get_active()

  def OnTicktypeEighthChanged(self, widget):
    self.ticktype_eighth = widget.get_active()

  def OnTicktypeTripletChanged(self, widget):
    self.ticktype_triplet = widget.get_active()

  def OnTicktypeSixteenthChanged(self, widget):
    self.ticktype_sixteenth = widget.get_active()

  def SetBeatLabel(self, label_value):
    label = '<span font_desc="Sans 50">'+str(label_value)+'</span>'
    self.wTree.get_widget("beat_label").set_label(label)

  def SetComboboxDefaults(self):
    self.wTree.get_widget("ticktype_accent").set_active(3)
    self.wTree.get_widget("ticktype_quarter").set_active(4)
    self.wTree.get_widget("ticktype_eighth").set_active(0)
    self.wTree.get_widget("ticktype_sixteenth").set_active(0)
    self.wTree.get_widget("ticktype_triplet").set_active(0)

  def ResetBeat(self):
    self.ticks = 0  #What is our tick count?
    self.beat = 0
    self.eighth_ticked = False
    self.sixteenth_ticked = False
    self.triplet_ticked = False

  def TapTempo(self, widget):
    self.OnPlay(0)
    log.debug('Tap Handler')
    this_tap = currentms()
    if self.last_tap and (this_tap - self.last_tap ) > 5000:
      self.taptempo_mode = False

    if self.taptempo_mode :
      dur = (this_tap - self.last_tap)
      self.tap_durs.append(dur)
      bpm = ms_to_bpm(mean(self.tap_durs)) # ms/min * beat/ms = beat/min
      log.debug('Got a tap %d which means our bpm:%d, %r', dur, bpm, self.tap_durs)
      self.wTree.get_widget("tempo").set_value(bpm)
    else:
      self.tap_durs = []
      self.taptempo_mode = True

    self.last_tap = currentms()
    self.ticks = 0
    self.taptempo_ticks = 1
    self.beat = 0

  def ticking_loop(self):
    self.last_time = currentms()
    now = currentms()
    while self.playing:
      if((now - self.last_time) > 25):
        self.last_time = now
        self.tick_stuff()
      #print 'debug - '+str(self.last_time)+' - '+str(time.time())
      if gtk.events_pending():
        gtk.main_iteration()

  def tick_stuff(self):
    #don't run if you don't need to
    if not self.playing: return False
    now = currentms()
    dur = bpm_to_dur(self.tempo)

    # not time to beat yet
    if (now - self.last_beat) < dur: return False
    #if tick number >= (calls to this function in a second*60 seconds in a minute)/the tempo
    if self.ticks >= round(((1000/TIMER_ACCURACY)*60)/self.tempo) or self.ticks == 0:
      #Reset these so that everything keeps ticking properly
      self.ticks = 0
      self.eighth_ticked = False
      self.sixteenth_ticked = False
      
      #move beat down
      if self.beat >= self.bpm or self.beat == 0:
        self.beat = 1
        tick_type = 'accent'
      else:
        self.beat += 1
        tick_type = 'quarter'

      #update the display
      self.SetBeatLabel(self.beat)

      #Play it
      self.GetTickSound(tick_type).play()
      
    #The above, but half as much for 8th note ticks
    elif self.eighth_ticked == False and self.ticks == round(((1000/TIMER_ACCURACY)*60)/(self.tempo * 2)):
      #Reset this for the 16th note
      #print "eighth"
      self.sixteenth_ticked = False
      self.triplet_ticked = False
      self.eighth_ticked = True
      self.GetTickSound('eighth').play()
        
    #The above, but find the modulus of above so it will work with the second tick, too
    elif self.sixteenth_ticked == False and self.ticks % (((1000/TIMER_ACCURACY)*60)/(self.tempo * 2)) >= ((1000/TIMER_ACCURACY)*60)/(self.tempo * 4):
      #print "sixteenth"
      self.sixteenth_ticked = True
      self.GetTickSound('sixteenth').play()
      
    #Triplets!  
    elif self.ticks == round(((1000/TIMER_ACCURACY)*60)/(self.tempo * 3)) or self.ticks == round(((1000/TIMER_ACCURACY)*60*2)/(self.tempo * 3)):
      #Reset this for the 16th note
      self.triplet_ticked = True
      self.GetTickSound('triplet').play()
    
    #Tick and keep going
    self.ticks += 1
    return True
    
  #Returns the link to the sound object for the given situation
  def GetTickSound(self, tick_type):
    if tick_type == 'accent':
      soundobject = self.GetSoundObjectByName(self.ticktype_accent, tick_type)
      soundobject.set_volume(self.volume_master * self.volume_accent)
      return soundobject
    if tick_type == 'quarter':
      soundobject = self.GetSoundObjectByName(self.ticktype_quarter, tick_type)
      soundobject.set_volume(self.volume_master * self.volume_quarter)
      return soundobject
    if tick_type == 'eighth':
      soundobject = self.GetSoundObjectByName(self.ticktype_eighth, tick_type)
      soundobject.set_volume(self.volume_master * self.volume_eighth)
      return soundobject
    if tick_type == 'triplet':
      soundobject = self.GetSoundObjectByName(self.ticktype_triplet, tick_type)
      soundobject.set_volume(self.volume_master * self.volume_triplet)
      return soundobject
    elif tick_type == 'sixteenth':
      soundobject = self.GetSoundObjectByName(self.ticktype_sixteenth, tick_type)
      soundobject.set_volume(self.volume_master * self.volume_sixteenth)
      return soundobject
    else:
      print "Error!"

  def GetSoundObjectByName(self, tick_name, tick_type):
    #Tick
    if tick_name == 1:
      return self.tick_sound
    #Tock
    elif tick_name == 2:
      return self.tock_sound
    #Pulse
    elif tick_name == 3:
      return self.pulse_sound
    #Ping
    elif tick_name == 4:
      return self.ping_sound
    #Cowbell
    elif tick_name == 5:
      return self.cowbell_sound
    #Claves
    elif tick_name == 6:
      return self.claves_sound
    #Agogo Low
    elif tick_name == 7:
      return self.agogolow_sound
    #Agogo High
    elif tick_name == 8:
      return self.agogohigh_sound
    #Coffee Cup
    elif tick_name == 9:
      return self.coffeecup_sound
    #Shaker
    elif tick_name == 10:
      return self.shaker_sound
    #Voice
    elif tick_name == 11:
      if tick_type == 'quarter' or tick_type == 'accent':
        if self.beat == 1:
          return self.one_sound
        elif self.beat == 2:
          return self.two_sound
        elif self.beat == 3:
          return self.three_sound
        elif self.beat == 4:
          return self.four_sound
        elif self.beat == 5:
          return self.five_sound
        elif self.beat == 6:
          return self.six_sound
        elif self.beat == 7:
          return self.seven_sound
        elif self.beat == 8:
          return self.eight_sound
        else:
          return self.num_sound
      elif tick_type == 'eighth':
        return self.and_sound
      elif tick_type == 'sixteenth':
        if self.eighth_ticked == False:
          return self.e_sound
        else:
          return self.a_sound
      elif tick_type == 'triplet':
        if self.eighth_ticked == False:
          return self.tee_sound
        else:
          return self.ta_sound
      
    #if we still haven't returned anything
    return self.null_sound

start = Main()
gtk.main()
