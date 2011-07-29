#!/usr/bin/python

import pygtk
import gtk
import gtk.glade
import time
import pygame.mixer
#import wav
import logging

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(name)-10s %(levelname)-8s %(message)s",
                    datefmt='%H:%M:%S',
                    handlers= logging.StreamHandler())
log = logging.getLogger('mrbeat');
log.debug('starting')

#defines
TIMER_ACCURACY = 5
BEAT_LENGTH = 1
FREQ = 22050
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
  return int(round((1000*60) / ms))

def bpm_to_ms(bpm):
  return int(round((1000.0 * 60.0)/float(bpm))) # ms/min / beats/min = ms/beat 

def beat_to_tick_type(i):
  if i == 0: return 'accent'
  elif i % 4 == 0: return 'quarter'
  elif i % 2 == 0: return 'eighth'
  else: return 'sixteenth'



pygame.init()

    #Load tick sounds
tick_sound = pygame.mixer.Sound('sounds/click4.wav')
tock_sound = pygame.mixer.Sound('sounds/click3.wav')
pulse_sound = pygame.mixer.Sound('sounds/pulse.wav')
ping_sound = pygame.mixer.Sound('sounds/ping.wav')
cowbell_sound = pygame.mixer.Sound('sounds/cowbell.wav')
claves_sound = pygame.mixer.Sound('sounds/claves.wav')
agogolow_sound = pygame.mixer.Sound('sounds/agogo1.wav')
agogohigh_sound = pygame.mixer.Sound('sounds/agogo2.wav')
coffeecup_sound = pygame.mixer.Sound('sounds/coffeecup.wav')
shaker_sound = pygame.mixer.Sound('sounds/shaker.wav')
one_sound = pygame.mixer.Sound('sounds/one.wav')
two_sound = pygame.mixer.Sound('sounds/two.wav')
three_sound = pygame.mixer.Sound('sounds/three.wav')
four_sound = pygame.mixer.Sound('sounds/four.wav')
five_sound = pygame.mixer.Sound('sounds/five.wav')
six_sound = pygame.mixer.Sound('sounds/six.wav')
seven_sound = pygame.mixer.Sound('sounds/seven.wav')
eight_sound = pygame.mixer.Sound('sounds/eight.wav')
num_sound = pygame.mixer.Sound('sounds/num.wav')
and_sound = pygame.mixer.Sound('sounds/and.wav')
e_sound = pygame.mixer.Sound('sounds/e.wav')
a_sound = pygame.mixer.Sound('sounds/a.wav')
tee_sound = pygame.mixer.Sound('sounds/tee.wav')
ta_sound = pygame.mixer.Sound('sounds/ta.wav')
null_sound = pygame.mixer.Sound('sounds/nothing.wav')
vocal_sound_list = [one_sound, two_sound, three_sound, 
                    four_sound, five_sound, six_sound, 
                    seven_sound, eight_sound]
sound_list=[tick_sound, tock_sound, pulse_sound, ping_sound,
            cowbell_sound, claves_sound, agogolow_sound,
            agogohigh_sound, cowbell_sound, shaker_sound]

def construct_rhythm(tempo, bpm):
  f = '\x00\x00'*46 # = 1ms white noise
  bpm = int(bpm)
  dur = bpm_to_ms( tempo * 4 / bpm )
  ssnd = ping_sound.get_buffer().raw
  beat = ssnd + (f * dur)  
  srhythm = beat * bpm
  rhythm = None
  try:
    rhythm = pygame.mixer.Sound(srhythm)
  except:
    pass
  rhythm.play()
  return rhythm

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
    self.taptempo_mode = False
    self.clock = pygame.time.Clock()
    self.last_time = 0.0
    self.last_tap = None
    self.last_beat = 0
    self.first_beat = 0
    self.current_beat = 0
    
    #Show the main window
    
    self.window = self.wTree.get_widget("mainwindow")
    self.window.connect("destroy", self.OnQuit)
    self.window.show_all()

  def OnPlay(self, widget):
    self.playing = True
    self.ResetBeat()
    #self.ticking_loop()
    self.rhthym = self.CreateRhythm()
    try:
      #self.rhthym.play(loops=-1)
      pass
    except TypeError, e:
      pass

    
      
  def OnStop(self, widget):
    self.playing = False
    self.rhthym.stop()
    self.SetBeatLabel('-')
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
    self.first_beat = currentms();
    self.eighth_ticked = False
    self.sixteenth_ticked = False
    self.triplet_ticked = False

  def TapTempo(self, widget):
    self.OnPlay(0)
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

  def ticking_loop(self):
    while self.playing:
      now = currentms()
      if (now - self.last_time) > TIMER_ACCURACY :
        self.last_time = now
        self.tick_stuff()
      if gtk.events_pending():
        gtk.main_iteration()

  def tick_stuff(self):
    #log.debug('Tick: %s  %s  %s %s %s %s', self.playing, self.tempo, 
    #          bpm_to_ms( self.tempo / self.bpm )  ,
    #          self.bpm, self.current_beat, self.CurrentQuarter())
    #don't run if you don't need to
    if not self.playing: return False
    now = currentms()
    bpm = int(self.bpm)
    dur = bpm_to_ms( self.tempo / bpm ) 
    # not time to beat yet
    if (now - self.last_beat) < dur: return False
    self.last_beat = now
    
    if self.current_beat >= bpm * 4: # handle 16ths of instead of quarters
      log.debug('Beat reset[%s]', currentms()-self.first_beat)
      self.first_beat = currentms();
      self.current_beat = 0
    tick_type = beat_to_tick_type(self.current_beat)

    self.SetBeatLabel(self.CurrentQuarter()+1)
    #self.PlayTickSound(tick_type, int(dur))
    self.current_beat+=1
      
    #Triplets!  
#    elif self.ticks == round(((1000/TIMER_ACCURACY)*60)/(self.tempo * 3)) or self.ticks == round(((1000/TIMER_ACCURACY)*60*2)/(self.tempo * 3)):
#      #Reset this for the 16th note
#      self.triplet_ticked = True
#      self.GetTickSound('triplet').play()
#    
#    #Tick and keep going
#    self.ticks += 1
#    return True
  def CurrentQuarter(self):
    #converting from 16ths back into quarters
    return (int(self.current_beat) / 4)

  #Returns the link to the sound object for the given situation
  def PlayTickSound (self, tick_type, dur=0):
    snd = self.GetTickSound(tick_type)
    if snd:
      log.debug('Beat play [%s] - %s', currentms()-self.first_beat, tick_type)
      snd.play(maxtime=dur)

  def GetTickSound(self, tick_type):
    ctl = getattr(self, 'ticktype_'+tick_type)
    vol = getattr(self, 'volume_'+tick_type)
    vol = self.volume_master * vol
    if vol == 0 or ctl == 0: return None #disabled
    snd = self.GetSoundObjectByName(ctl, tick_type)
    if snd: snd.set_volume(self.volume_master * vol)
    return snd

  def GetTickSoundBytes(self, tick_type):
    snd = self.GetTickSound(tick_type).get_buffer().raw()
    if snd: return snd.get_buffer().bytes()

  def GetSoundObjectByName(self, tick_name, tick_type):
    if tick_name == 0 : return None; # disabled
    if tick_name<11:
      return sound_list[tick_name-1]
    else:# tick_name == 11:
      if tick_type=='accent' or tick_type=='quarter':
        return vocal_sound_list[self.CurrentQuarter()]
      elif tick_type == 'eighth':
        return and_sound
      elif tick_type == 'sixteenth':
        if eighth_ticked == False:
          return e_sound
        else:
          return a_sound
      elif tick_type == 'triplet':
        if eighth_ticked == False:
          return tee_sound
        else:
          return ta_sound
    #if we still haven't returned anything
    return None


  def CreateRhythm(self):
    fperMs = 46.0
    wait = '\x00\x00'
    bpm = int(self.bpm)
    # *4 to handle 16ths
    dur = bpm_to_ms( self.tempo * bpm )
    bytes=''
    for i in range(0,16):
      tt = beat_to_tick_type(i)
      snd = self.GetTickSound(tt)
      if snd:
        lenMs = int(snd.get_length()*1000)
        n = int((dur-lenMs) * fperMs)
        bytes += snd.get_buffer().raw + (n*wait)
      else:
        n = int(dur * fperMs)
        bytes += (n*wait)

    try:
      rhythm = pygame.mixer.Sound(bytes)
      rhythm.play()
    except TypeError, e:
      log.exception(e)
    return rhythm

    

start = Main()
gtk.main()
