import ClientCaches
import ClientConstants as CC
import ClientData
import ClientDownloading
import ClientGUICommon
import ClientGUIDialogs
import ClientGUIPredicates
import ClientGUITopLevelWindows
import ClientMedia
import ClientThreading
import collections
import HydrusConstants as HC
import HydrusData
import HydrusExceptions
import HydrusGlobals
import HydrusNATPunch
import HydrusPaths
import HydrusSerialisable
import HydrusTags
import itertools
import os
import random
import string
import time
import traceback
import wx
import wx.lib.scrolledpanel

class EditPanel( wx.lib.scrolledpanel.ScrolledPanel ):
    
    def __init__( self, parent ):
        
        wx.lib.scrolledpanel.ScrolledPanel.__init__( self, parent )
        
    
    def GetValue( self ):
        
        raise NotImplementedError()
        
    
class EditFrameLocationPanel( EditPanel ):
    
    def __init__( self, parent, info ):
        
        EditPanel.__init__( self, parent )
        
        self._original_info = info
        
        self._remember_size = wx.CheckBox( self, label = 'remember size' )
        self._remember_position = wx.CheckBox( self, label = 'remember position' )
        
        self._last_size = ClientGUICommon.NoneableSpinCtrl( self, 'last size', none_phrase = 'none set', min = 100, max = 1000000, unit = None, num_dimensions = 2 )
        self._last_position = ClientGUICommon.NoneableSpinCtrl( self, 'last position', none_phrase = 'none set', min = 100, max = 1000000, unit = None, num_dimensions = 2 )
        
        self._default_gravity_x = ClientGUICommon.BetterChoice( self )
        
        self._default_gravity_x.Append( 'by default, expand to width of parent', 1 )
        self._default_gravity_x.Append( 'by default, expand width as much as needed', -1 )
        
        self._default_gravity_y = ClientGUICommon.BetterChoice( self )
        
        self._default_gravity_y.Append( 'by default, expand to height of parent', 1 )
        self._default_gravity_y.Append( 'by default, expand height as much as needed', -1 )
        
        self._default_position = ClientGUICommon.BetterChoice( self )
        
        self._default_position.Append( 'by default, position off the top-left corner of parent', 'topleft' )
        self._default_position.Append( 'by default, position centered on the parent', 'center' )
        
        self._maximised = wx.CheckBox( self, label = 'start maximised' )
        self._fullscreen = wx.CheckBox( self, label = 'start fullscreen' )
        
        #
        
        ( name, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = self._original_info
        
        self._remember_size.SetValue( remember_size )
        self._remember_position.SetValue( remember_position )
        
        self._last_size.SetValue( last_size )
        self._last_position.SetValue( last_position )
        
        ( x, y ) = default_gravity
        
        self._default_gravity_x.SelectClientData( x )
        self._default_gravity_y.SelectClientData( y )
        
        self._default_position.SelectClientData( default_position )
        
        self._maximised.SetValue( maximised )
        self._fullscreen.SetValue( fullscreen )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        text = 'Setting frame location info for ' + name + '.'
        
        vbox.AddF( wx.StaticText( self, label = text ), CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._remember_size, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._remember_position, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._last_size, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._last_position, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._default_gravity_x, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._default_gravity_y, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._default_position, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._maximised, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._fullscreen, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
    
    def GetValue( self ):
        
        ( name, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = self._original_info
        
        remember_size = self._remember_size.GetValue()
        remember_position = self._remember_position.GetValue()
        
        last_size = self._last_size.GetValue()
        last_position = self._last_position.GetValue()
        
        x = self._default_gravity_x.GetChoice()
        y = self._default_gravity_y.GetChoice()
        
        default_gravity = [ x, y ]
        
        default_position = self._default_position.GetChoice()
        
        maximised = self._maximised.GetValue()
        fullscreen = self._fullscreen.GetValue()
        
        return ( name, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen )
        
    
class EditSeedCachePanel( EditPanel ):
    
    def __init__( self, parent, controller, seed_cache ):
        
        EditPanel.__init__( self, parent )
        
        self._controller = controller
        self._seed_cache = seed_cache
        
        self._text = wx.StaticText( self, label = 'initialising' )
        self._seed_cache_control = ClientGUICommon.SeedCacheControl( self, self._seed_cache )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.AddF( self._text, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._seed_cache_control, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        self._controller.sub( self, 'NotifySeedUpdated', 'seed_cache_seed_updated' )
        
        wx.CallAfter( self._UpdateText )
        
    
    def _UpdateText( self ):
        
        ( status, ( total_processed, total ) ) = self._seed_cache.GetStatus()
        
        self._text.SetLabelText( status )
        
        self.Layout()
        
    
    def GetValue( self ):
        
        return self._seed_cache
        
    
    def NotifySeedUpdated( self, seed ):
        
        self._UpdateText()
        
    
class ManagePanel( wx.lib.scrolledpanel.ScrolledPanel ):
    
    def __init__( self, parent ):
        
        wx.lib.scrolledpanel.ScrolledPanel.__init__( self, parent )
        
    
    def CommitChanges( self ):
        
        raise NotImplementedError()
        
    
class ManageOptionsPanel( ManagePanel ):
    
    def __init__( self, parent ):
        
        ManagePanel.__init__( self, parent )
        
        self._new_options = HydrusGlobals.client_controller.GetNewOptions()
        
        self._listbook = ClientGUICommon.ListBook( self )
        
        self._listbook.AddPage( 'connection', 'connection', self._ConnectionPanel( self._listbook ) )
        self._listbook.AddPage( 'files and trash', 'files and trash', self._FilesAndTrashPanel( self._listbook ) )
        self._listbook.AddPage( 'speed and memory', 'speed and memory', self._SpeedAndMemoryPanel( self._listbook, self._new_options ) )
        self._listbook.AddPage( 'maintenance and processing', 'maintenance and processing', self._MaintenanceAndProcessingPanel( self._listbook ) )
        self._listbook.AddPage( 'media', 'media', self._MediaPanel( self._listbook ) )
        self._listbook.AddPage( 'gui', 'gui', self._GUIPanel( self._listbook ) )
        #self._listbook.AddPage( 'sound', 'sound', self._SoundPanel( self._listbook ) )
        self._listbook.AddPage( 'default file system predicates', 'default file system predicates', self._DefaultFileSystemPredicatesPanel( self._listbook, self._new_options ) )
        self._listbook.AddPage( 'default tag import options', 'default tag import options', self._DefaultTagImportOptionsPanel( self._listbook, self._new_options ) )
        self._listbook.AddPage( 'colours', 'colours', self._ColoursPanel( self._listbook ) )
        self._listbook.AddPage( 'local server', 'local server', self._ServerPanel( self._listbook ) )
        self._listbook.AddPage( 'sort/collect', 'sort/collect', self._SortCollectPanel( self._listbook ) )
        self._listbook.AddPage( 'shortcuts', 'shortcuts', self._ShortcutsPanel( self._listbook ) )
        self._listbook.AddPage( 'file storage locations', 'file storage locations', self._ClientFilesPanel( self._listbook ) )
        self._listbook.AddPage( 'downloading', 'downloading', self._DownloadingPanel( self._listbook, self._new_options ) )
        self._listbook.AddPage( 'tags', 'tags', self._TagsPanel( self._listbook, self._new_options ) )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.AddF( self._listbook, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        

    class _ClientFilesPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._client_files = ClientGUICommon.SaneListCtrl( self, 200, [ ( 'path', -1 ), ( 'weight', 80 ) ] )
            
            self._add = wx.Button( self, label = 'add' )
            self._add.Bind( wx.EVT_BUTTON, self.EventAdd )
            
            self._edit = wx.Button( self, label = 'edit weight' )
            self._edit.Bind( wx.EVT_BUTTON, self.EventEditWeight )
            
            self._delete = wx.Button( self, label = 'delete' )
            self._delete.Bind( wx.EVT_BUTTON, self.EventDelete )
            
            #
            
            self._new_options = HydrusGlobals.client_controller.GetNewOptions()
            
            for ( location, weight ) in self._new_options.GetClientFilesLocationsToIdealWeights().items():
                
                self._client_files.Append( ( location, HydrusData.ConvertIntToPrettyString( int( weight ) ) ), ( location, weight ) )
                
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            text = 'Here you can change the folders where the client stores your files. Setting a higher weight increases the proportion of your collection that that folder stores.'
            text += os.linesep * 2
            text += 'If you add or remove folders here, it will take time for the client to incrementally rebalance your files across the new selection, but if you are in a hurry, you can force a full rebalance from the database->maintenance menu on the main gui.'
            
            st = wx.StaticText( self, label = text )
            
            st.Wrap( 400 )
            
            vbox.AddF( st, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            vbox.AddF( self._client_files, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            hbox.AddF( self._add, CC.FLAGS_MIXED )
            hbox.AddF( self._edit, CC.FLAGS_MIXED )
            hbox.AddF( self._delete, CC.FLAGS_MIXED )
            
            vbox.AddF( hbox, CC.FLAGS_BUTTON_SIZER )
            
            self.SetSizer( vbox )
            
        
        def EventAdd( self, event ):
            
            with wx.DirDialog( self, 'Select the file location' ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    path = HydrusData.ToUnicode( dlg.GetPath() )
                    
                    for ( location, weight ) in self._client_files.GetClientData():
                        
                        if path == location:
                            
                            wx.MessageBox( 'You already have that location entered!' )
                            
                            return
                            
                        
                    
                    with wx.NumberEntryDialog( self, 'Enter the weight of ' + path + '.', '', 'Enter Weight', value = 1, min = 1, max = 256 ) as dlg_num:
                        
                        if dlg_num.ShowModal() == wx.ID_OK:
                            
                            weight = dlg_num.GetValue()
                            
                            weight = float( weight )
                            
                            self._client_files.Append( ( path, HydrusData.ConvertIntToPrettyString( int( weight ) ) ), ( path, weight ) )
                            
                        
                    
                
            
        
        def EventDelete( self, event ):
            
            if len( self._client_files.GetAllSelected() ) < self._client_files.GetItemCount():
                
                self._client_files.RemoveAllSelected()
                
            
        
        def EventEditWeight( self, event ):
            
            for i in self._client_files.GetAllSelected():
                
                ( location, weight ) = self._client_files.GetClientData( i )
                
                with wx.NumberEntryDialog( self, 'Enter the weight of ' + location + '.', '', 'Enter Weight', value = int( weight ), min = 1, max = 256 ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        weight = dlg.GetValue()
                        
                        weight = float( weight )
                        
                        self._client_files.UpdateRow( i, ( location, HydrusData.ConvertIntToPrettyString( int( weight ) ) ), ( location, weight ) )
                        
                    
                
            
        
        def UpdateOptions( self ):
            
            locations_to_weights = {}
            
            for ( location, weight ) in self._client_files.GetClientData():
                
                locations_to_weights[ location ] = weight
                
            
            self._new_options.SetClientFilesLocationsToIdealWeights( locations_to_weights )
            
        

    class _ColoursPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._gui_colours = {}
            
            for ( name, rgb ) in HC.options[ 'gui_colours' ].items():
                
                ctrl = wx.ColourPickerCtrl( self )
                
                ctrl.SetMaxSize( ( 20, -1 ) )
                
                self._gui_colours[ name ] = ctrl
                
            
            self._namespace_colours = ClientGUICommon.ListBoxTagsColourOptions( self, HC.options[ 'namespace_colours' ] )
            
            self._edit_namespace_colour = wx.Button( self, label = 'edit selected' )
            self._edit_namespace_colour.Bind( wx.EVT_BUTTON, self.EventEditNamespaceColour )
            
            self._new_namespace_colour = wx.TextCtrl( self, style = wx.TE_PROCESS_ENTER )
            self._new_namespace_colour.Bind( wx.EVT_KEY_DOWN, self.EventKeyDownNamespace )
            
            #
            
            for ( name, rgb ) in HC.options[ 'gui_colours' ].items(): self._gui_colours[ name ].SetColour( wx.Colour( *rgb ) )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddF( wx.StaticText( self, label = 'thumbnail background (local: normal/selected, remote: normal/selected): ' ), CC.FLAGS_MIXED )
            
            hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            hbox.AddF( self._gui_colours[ 'thumb_background' ], CC.FLAGS_MIXED )
            hbox.AddF( self._gui_colours[ 'thumb_background_selected' ], CC.FLAGS_MIXED )
            hbox.AddF( self._gui_colours[ 'thumb_background_remote' ], CC.FLAGS_MIXED )
            hbox.AddF( self._gui_colours[ 'thumb_background_remote_selected' ], CC.FLAGS_MIXED )
            
            gridbox.AddF( hbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            gridbox.AddF( wx.StaticText( self, label = 'thumbnail border (local: normal/selected, remote: normal/selected): ' ), CC.FLAGS_MIXED )
            
            hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            hbox.AddF( self._gui_colours[ 'thumb_border' ], CC.FLAGS_MIXED )
            hbox.AddF( self._gui_colours[ 'thumb_border_selected' ], CC.FLAGS_MIXED )
            hbox.AddF( self._gui_colours[ 'thumb_border_remote' ], CC.FLAGS_MIXED )
            hbox.AddF( self._gui_colours[ 'thumb_border_remote_selected' ], CC.FLAGS_MIXED )
            
            gridbox.AddF( hbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            gridbox.AddF( wx.StaticText( self, label = 'thumbnail grid background: '), CC.FLAGS_MIXED )
            gridbox.AddF( self._gui_colours[ 'thumbgrid_background' ], CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'autocomplete background: '), CC.FLAGS_MIXED )
            gridbox.AddF( self._gui_colours[ 'autocomplete_background' ], CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'media viewer background: '), CC.FLAGS_MIXED )
            gridbox.AddF( self._gui_colours[ 'media_background' ], CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'media viewer text: '), CC.FLAGS_MIXED )
            gridbox.AddF( self._gui_colours[ 'media_text' ], CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'tags box background: '), CC.FLAGS_MIXED )
            gridbox.AddF( self._gui_colours[ 'tags_box' ], CC.FLAGS_MIXED )
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._namespace_colours, CC.FLAGS_EXPAND_BOTH_WAYS )
            vbox.AddF( self._new_namespace_colour, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._edit_namespace_colour, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def EventEditNamespaceColour( self, event ):
            
            results = self._namespace_colours.GetSelectedNamespaceColours()
            
            for ( namespace, colour ) in results:
                
                colour_data = wx.ColourData()
                
                colour_data.SetColour( colour )
                colour_data.SetChooseFull( True )
                
                with wx.ColourDialog( self, data = colour_data ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        colour_data = dlg.GetColourData()
                        
                        colour = colour_data.GetColour()
                        
                        self._namespace_colours.SetNamespaceColour( namespace, colour )
                        
                    
                
            
        
        def EventKeyDownNamespace( self, event ):
            
            if event.KeyCode in ( wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER ):
                
                namespace = self._new_namespace_colour.GetValue()
                
                if namespace != '':
                    
                    self._namespace_colours.SetNamespaceColour( namespace, wx.Colour( random.randint( 0, 255 ), random.randint( 0, 255 ), random.randint( 0, 255 ) ) )
                    
                    self._new_namespace_colour.SetValue( '' )
                    
                
            else: event.Skip()
            
        
        def UpdateOptions( self ):
            
            for ( name, ctrl ) in self._gui_colours.items():
                
                colour = ctrl.GetColour()
                
                rgb = ( colour.Red(), colour.Green(), colour.Blue() )
                
                HC.options[ 'gui_colours' ][ name ] = rgb
                
            
            HC.options[ 'namespace_colours' ] = self._namespace_colours.GetNamespaceColours()
            
        
    
    class _ConnectionPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._external_host = wx.TextCtrl( self )
            self._external_host.SetToolTipString( 'If you have trouble parsing your external ip using UPnP, you can force it to be this.' )
            
            proxy_panel = ClientGUICommon.StaticBox( self, 'proxy settings' )
            
            self._proxy_type = ClientGUICommon.BetterChoice( proxy_panel )
            
            self._proxy_address = wx.TextCtrl( proxy_panel )
            self._proxy_port = wx.SpinCtrl( proxy_panel, min = 0, max = 65535 )
            
            self._proxy_username = wx.TextCtrl( proxy_panel )
            self._proxy_password = wx.TextCtrl( proxy_panel )
            
            #
            
            if HC.options[ 'external_host' ] is not None:
                
                self._external_host.SetValue( HC.options[ 'external_host' ] )
                
            
            self._proxy_type.Append( 'http', 'http' )
            self._proxy_type.Append( 'socks4', 'socks4' )
            self._proxy_type.Append( 'socks5', 'socks5' )
            
            if HC.options[ 'proxy' ] is not None:
                
                ( proxytype, host, port, username, password ) = HC.options[ 'proxy' ]
                
                self._proxy_type.SelectClientData( proxytype )
                
                self._proxy_address.SetValue( host )
                self._proxy_port.SetValue( port )
                
                if username is not None:
                    
                    self._proxy_username.SetValue( username )
                    
                
                if password is not None:
                    
                    self._proxy_password.SetValue( password )
                    
                
            else:
                
                self._proxy_type.Select( 0 )
                
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( proxy_panel, label = 'Proxy type: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._proxy_type, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( proxy_panel, label = 'Address: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._proxy_address, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( proxy_panel, label = 'Port: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._proxy_port, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( proxy_panel, label = 'Username (optional): ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._proxy_username, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( proxy_panel, label = 'Password (optional): ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._proxy_password, CC.FLAGS_MIXED )
            
            text = 'You have to restart the client for proxy settings to take effect.'
            text += os.linesep
            text += 'This is in a buggy prototype stage right now, pending a rewrite of the networking engine.'
            text += os.linesep
            text += 'Please send me your feedback.'
            
            proxy_panel.AddF( wx.StaticText( proxy_panel, label = text ), CC.FLAGS_EXPAND_PERPENDICULAR )
            proxy_panel.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'External IP/host override: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._external_host, CC.FLAGS_MIXED )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            vbox.AddF( proxy_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def UpdateOptions( self ):
            
            if self._proxy_address.GetValue() == '':
                
                HC.options[ 'proxy' ] = None
                
            else:
                
                proxytype = self._proxy_type.GetChoice()
                address = self._proxy_address.GetValue()
                port = self._proxy_port.GetValue()
                username = self._proxy_username.GetValue()
                password = self._proxy_password.GetValue()
                
                if username == '': username = None
                if password == '': password = None
                
                HC.options[ 'proxy' ] = ( proxytype, address, port, username, password )
                
            
            external_host = self._external_host.GetValue()
            
            if external_host == '':
                
                external_host = None
                
            
            HC.options[ 'external_host' ] = external_host
            
        
    
    class _DownloadingPanel( wx.Panel ):
        
        def __init__( self, parent, new_options ):
            
            wx.Panel.__init__( self, parent )
            
            self._new_options = new_options
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            general = ClientGUICommon.StaticBox( self, 'general' )
            
            self._website_download_polite_wait = wx.SpinCtrl( general, min = 1, max = 30 )
            
            self._waiting_politely_text = wx.CheckBox( general )
            
            #
            
            gallery_downloader = ClientGUICommon.StaticBox( self, 'gallery downloader' )
            
            self._gallery_file_limit = ClientGUICommon.NoneableSpinCtrl( gallery_downloader, 'default file limit', none_phrase = 'no limit', min = 1, max = 1000000 )
            
            #
            
            thread_checker = ClientGUICommon.StaticBox( self, 'thread checker' )
            
            self._thread_times_to_check = wx.SpinCtrl( thread_checker, min = 0, max = 100 )
            self._thread_times_to_check.SetToolTipString( 'how many times the thread checker will check' )
            
            self._thread_check_period = ClientGUICommon.TimeDeltaButton( thread_checker, min = 30, hours = True, minutes = True, seconds = True )
            self._thread_check_period.SetToolTipString( 'how long the checker will wait between checks' )
            
            #
            
            self._website_download_polite_wait.SetValue( HC.options[ 'website_download_polite_wait' ] )
            self._waiting_politely_text.SetValue( self._new_options.GetBoolean( 'waiting_politely_text' ) )
            
            self._gallery_file_limit.SetValue( HC.options[ 'gallery_file_limit' ] )
            
            ( times_to_check, check_period ) = HC.options[ 'thread_checker_timings' ]
            
            self._thread_times_to_check.SetValue( times_to_check )
            
            self._thread_check_period.SetValue( check_period )
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( general, label = 'seconds to politely wait between gallery/thread url requests: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._website_download_polite_wait, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( general, label = 'instead of the traffic light waiting politely indicator, use text: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._waiting_politely_text, CC.FLAGS_MIXED )
            
            general.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
            
            #
            
            gallery_downloader.AddF( self._gallery_file_limit, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( thread_checker, label = 'default number of times to check: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._thread_times_to_check, CC.FLAGS_MIXED )
            gridbox.AddF( wx.StaticText( thread_checker, label = 'default wait between checks: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._thread_check_period, CC.FLAGS_MIXED )
            
            thread_checker.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( general, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( gallery_downloader, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( thread_checker, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def UpdateOptions( self ):
            
            HC.options[ 'website_download_polite_wait' ] = self._website_download_polite_wait.GetValue()
            self._new_options.SetBoolean( 'waiting_politely_text', self._waiting_politely_text.GetValue() )
            HC.options[ 'gallery_file_limit' ] = self._gallery_file_limit.GetValue()
            HC.options[ 'thread_checker_timings' ] = ( self._thread_times_to_check.GetValue(), self._thread_check_period.GetValue() )
            
        
    
    class _MaintenanceAndProcessingPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._jobs_panel = ClientGUICommon.StaticBox( self, 'when to run high cpu jobs' )
            self._maintenance_panel = ClientGUICommon.StaticBox( self, 'maintenance period' )
            self._processing_panel = ClientGUICommon.StaticBox( self, 'processing' )
            
            self._idle_panel = ClientGUICommon.StaticBox( self._jobs_panel, 'idle' )
            self._shutdown_panel = ClientGUICommon.StaticBox( self._jobs_panel, 'shutdown' )
            
            #
            
            self._idle_normal = wx.CheckBox( self._idle_panel )
            self._idle_normal.Bind( wx.EVT_CHECKBOX, self.EventIdleNormal )
            
            self._idle_period = ClientGUICommon.NoneableSpinCtrl( self._idle_panel, '', min = 1, max = 1000, multiplier = 60, unit = 'minutes', none_phrase = 'ignore normal browsing' )
            self._idle_mouse_period = ClientGUICommon.NoneableSpinCtrl( self._idle_panel, '', min = 1, max = 1000, multiplier = 60, unit = 'minutes', none_phrase = 'ignore mouse movements' )
            self._idle_cpu_max = ClientGUICommon.NoneableSpinCtrl( self._idle_panel, '', min = 5, max = 99, unit = '%', none_phrase = 'ignore cpu usage' )
            
            #
            
            self._idle_shutdown = ClientGUICommon.BetterChoice( self._shutdown_panel )
            
            for idle_id in ( CC.IDLE_NOT_ON_SHUTDOWN, CC.IDLE_ON_SHUTDOWN, CC.IDLE_ON_SHUTDOWN_ASK_FIRST ):
                
                self._idle_shutdown.Append( CC.idle_string_lookup[ idle_id ], idle_id )
                
            
            self._idle_shutdown.Bind( wx.EVT_CHOICE, self.EventIdleShutdown )
            
            self._idle_shutdown_max_minutes = wx.SpinCtrl( self._shutdown_panel, min = 1, max = 1440 )
            
            #
            
            self._maintenance_vacuum_period = ClientGUICommon.NoneableSpinCtrl( self._maintenance_panel, '', min = 1, max = 365, multiplier = 86400, none_phrase = 'do not automatically vacuum' )
            
            #
            
            self._processing_phase = wx.SpinCtrl( self._processing_panel, min = 0, max = 100000 )
            self._processing_phase.SetToolTipString( 'how long this client will delay processing updates after they are due. useful if you have multiple clients and do not want them to process at the same time' )
            
            #
            
            self._idle_normal.SetValue( HC.options[ 'idle_normal' ] )
            self._idle_period.SetValue( HC.options[ 'idle_period' ] )
            self._idle_mouse_period.SetValue( HC.options[ 'idle_mouse_period' ] )
            self._idle_cpu_max.SetValue( HC.options[ 'idle_cpu_max' ] )
            
            self._idle_shutdown.SelectClientData( HC.options[ 'idle_shutdown' ] )
            self._idle_shutdown_max_minutes.SetValue( HC.options[ 'idle_shutdown_max_minutes' ] )
            
            self._maintenance_vacuum_period.SetValue( HC.options[ 'maintenance_vacuum_period' ] )
            
            self._processing_phase.SetValue( HC.options[ 'processing_phase' ] )
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self._idle_panel, label = 'Run maintenance jobs when the client is idle and the system is not otherwise busy?: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._idle_normal, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self._idle_panel, label = 'Assume the client is idle if no general browsing activity has occured in the past: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._idle_period, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self._idle_panel, label = 'Assume the client is idle if the mouse has not been moved in the past: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._idle_mouse_period, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self._idle_panel, label = 'Assume the system is busy if any CPU core has recent average usage above: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._idle_cpu_max, CC.FLAGS_MIXED )
            
            self._idle_panel.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self._shutdown_panel, label = 'Run jobs on shutdown?: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._idle_shutdown, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self._shutdown_panel, label = 'Max number of minutes to run shutdown jobs: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._idle_shutdown_max_minutes, CC.FLAGS_MIXED )
            
            self._shutdown_panel.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            #
            
            text = 'CPU-heavy jobs like maintenance routines and repository synchronisation processing will stutter or lock up your gui, so they do not normally run when you are searching for and looking at files.'
            text += os.linesep * 2
            text += 'You can set them to run only when the client is idle, or only during shutdown, or neither, or both.'
            text += os.linesep * 2
            text += 'If the client switches from idle to not idle, it will try to abandon any jobs it is half way through.'
            text += os.linesep * 2
            text += 'If the client believes the system is busy, it will not start jobs.'
            
            st = wx.StaticText( self._jobs_panel, label = text )
            
            st.Wrap( 550 )
            
            self._jobs_panel.AddF( st, CC.FLAGS_EXPAND_PERPENDICULAR )
            self._jobs_panel.AddF( self._idle_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            self._jobs_panel.AddF( self._shutdown_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self._maintenance_panel, label = 'Number of days to wait between vacuums: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._maintenance_vacuum_period, CC.FLAGS_MIXED )
            
            self._maintenance_panel.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self._processing_panel, label = 'Delay repository update processing by (s): ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._processing_phase, CC.FLAGS_MIXED )
            
            self._processing_panel.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( self._jobs_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._maintenance_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._processing_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
            self._EnableDisableIdleNormal()
            self._EnableDisableIdleShutdown()
            
        
        def _EnableDisableIdleNormal( self ):
            
            if self._idle_normal.GetValue() == True:
                
                self._idle_period.Enable()
                self._idle_mouse_period.Enable()
                self._idle_cpu_max.Enable()
                
            else:
                
                self._idle_period.Disable()
                self._idle_mouse_period.Disable()
                self._idle_cpu_max.Disable()
                
            
        
        def _EnableDisableIdleShutdown( self ):
            
            if self._idle_shutdown.GetChoice() == CC.IDLE_NOT_ON_SHUTDOWN:
                
                self._idle_shutdown_max_minutes.Disable()
                
            else:
                
                self._idle_shutdown_max_minutes.Enable()
                
            
        
        def EventIdleNormal( self, event ):
            
            self._EnableDisableIdleNormal()
            
        
        def EventIdleShutdown( self, event ):
            
            self._EnableDisableIdleShutdown()
            
        
        def UpdateOptions( self ):
            
            HC.options[ 'idle_normal' ] = self._idle_normal.GetValue()
            
            HC.options[ 'idle_period' ] = self._idle_period.GetValue()
            HC.options[ 'idle_mouse_period' ] = self._idle_mouse_period.GetValue()
            HC.options[ 'idle_cpu_max' ] = self._idle_cpu_max.GetValue()
            
            HC.options[ 'idle_shutdown' ] = self._idle_shutdown.GetChoice()
            HC.options[ 'idle_shutdown_max_minutes' ] = self._idle_shutdown_max_minutes.GetValue()
            
            HC.options[ 'maintenance_vacuum_period' ] = self._maintenance_vacuum_period.GetValue()
            
            HC.options[ 'processing_phase' ] = self._processing_phase.GetValue()
            
        
    
    class _DefaultFileSystemPredicatesPanel( wx.Panel ):
        
        def __init__( self, parent, new_options ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._new_options = new_options
            
            self._filter_inbox_and_archive_predicates = wx.CheckBox( self, label = 'hide inbox and archive predicates if either has no files' )
            
            self._filter_inbox_and_archive_predicates.SetValue( self._new_options.GetBoolean( 'filter_inbox_and_archive_predicates' ) )
            
            self._file_system_predicate_age = ClientGUIPredicates.PanelPredicateSystemAge( self )
            self._file_system_predicate_duration = ClientGUIPredicates.PanelPredicateSystemDuration( self )
            self._file_system_predicate_height = ClientGUIPredicates.PanelPredicateSystemHeight( self )
            self._file_system_predicate_limit = ClientGUIPredicates.PanelPredicateSystemLimit( self )
            self._file_system_predicate_mime = ClientGUIPredicates.PanelPredicateSystemMime( self )
            self._file_system_predicate_num_pixels = ClientGUIPredicates.PanelPredicateSystemNumPixels( self )
            self._file_system_predicate_num_tags = ClientGUIPredicates.PanelPredicateSystemNumTags( self )
            self._file_system_predicate_num_words = ClientGUIPredicates.PanelPredicateSystemNumWords( self )
            self._file_system_predicate_ratio = ClientGUIPredicates.PanelPredicateSystemRatio( self )
            self._file_system_predicate_similar_to = ClientGUIPredicates.PanelPredicateSystemSimilarTo( self )
            self._file_system_predicate_size = ClientGUIPredicates.PanelPredicateSystemSize( self )
            self._file_system_predicate_width = ClientGUIPredicates.PanelPredicateSystemWidth( self )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( self._filter_inbox_and_archive_predicates, CC.FLAGS_MIXED )
            vbox.AddF( ( 20, 20 ), CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_age, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_duration, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_height, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_limit, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_mime, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_num_pixels, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_num_tags, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_num_words, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_ratio, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_similar_to, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_size, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._file_system_predicate_width, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def UpdateOptions( self ):
            
            self._new_options.SetBoolean( 'filter_inbox_and_archive_predicates', self._filter_inbox_and_archive_predicates.GetValue() )
            
            system_predicates = HC.options[ 'file_system_predicates' ]
            
            system_predicates[ 'age' ] = self._file_system_predicate_age.GetInfo()
            system_predicates[ 'duration' ] = self._file_system_predicate_duration.GetInfo()
            system_predicates[ 'hamming_distance' ] = self._file_system_predicate_similar_to.GetInfo()[1]
            system_predicates[ 'height' ] = self._file_system_predicate_height.GetInfo()
            system_predicates[ 'limit' ] = self._file_system_predicate_limit.GetInfo()
            system_predicates[ 'mime' ] = self._file_system_predicate_mime.GetInfo()
            system_predicates[ 'num_pixels' ] = self._file_system_predicate_num_pixels.GetInfo()
            system_predicates[ 'num_tags' ] = self._file_system_predicate_num_tags.GetInfo()
            system_predicates[ 'num_words' ] = self._file_system_predicate_num_words.GetInfo()
            system_predicates[ 'ratio' ] = self._file_system_predicate_ratio.GetInfo()
            system_predicates[ 'size' ] = self._file_system_predicate_size.GetInfo()
            system_predicates[ 'width' ] = self._file_system_predicate_width.GetInfo()
            
            HC.options[ 'file_system_predicates' ] = system_predicates
            
        
    
    class _DefaultTagImportOptionsPanel( wx.Panel ):
        
        def __init__( self, parent, new_options ):
            
            wx.Panel.__init__( self, parent )
            
            self._new_options = new_options
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._import_tag_options = wx.ListBox( self )
            self._import_tag_options.Bind( wx.EVT_LEFT_DCLICK, self.EventDelete )
            
            self._add = wx.Button( self, label = 'add' )
            self._add.Bind( wx.EVT_BUTTON, self.EventAdd )
            
            self._edit = wx.Button( self, label = 'edit' )
            self._edit.Bind( wx.EVT_BUTTON, self.EventEdit )
            
            self._delete = wx.Button( self, label = 'delete' )
            self._delete.Bind( wx.EVT_BUTTON, self.EventDelete )
            
            #
            
            for ( gallery_identifier, import_tag_options ) in self._new_options.GetDefaultImportTagOptions().items():
                
                name = gallery_identifier.ToString()
                
                self._import_tag_options.Append( name, ( gallery_identifier, import_tag_options ) )
                
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( self._import_tag_options, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            hbox.AddF( self._add, CC.FLAGS_BUTTON_SIZER )
            hbox.AddF( self._edit, CC.FLAGS_BUTTON_SIZER )
            hbox.AddF( self._delete, CC.FLAGS_BUTTON_SIZER )
            
            vbox.AddF( hbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def EventAdd( self, event ):
            
            gallery_identifiers = []
            
            for site_type in [ HC.SITE_TYPE_DEFAULT, HC.SITE_TYPE_DEVIANT_ART, HC.SITE_TYPE_HENTAI_FOUNDRY, HC.SITE_TYPE_NEWGROUNDS, HC.SITE_TYPE_PIXIV, HC.SITE_TYPE_TUMBLR ]:
                
                gallery_identifiers.append( ClientDownloading.GalleryIdentifier( site_type ) )
                
            
            gallery_identifiers.append( ClientDownloading.GalleryIdentifier( HC.SITE_TYPE_BOORU ) )
            
            boorus = HydrusGlobals.client_controller.Read( 'remote_boorus' )
            
            for booru_name in boorus.keys():
                
                gallery_identifiers.append( ClientDownloading.GalleryIdentifier( HC.SITE_TYPE_BOORU, additional_info = booru_name ) )
                
            
            ordered_names = [ gallery_identifier.ToString() for gallery_identifier in gallery_identifiers ]
            
            names_to_gallery_identifiers = { gallery_identifier.ToString() : gallery_identifier for gallery_identifier in gallery_identifiers }
            
            with ClientGUIDialogs.DialogSelectFromListOfStrings( self, 'select tag domain', ordered_names ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    name = dlg.GetString()
                    
                    for i in range( self._import_tag_options.GetCount() ):
                        
                        if name == self._import_tag_options.GetString( i ):
                            
                            wx.MessageBox( 'You already have default tag import options set up for that domain!' )
                            
                            return
                            
                        
                    
                    gallery_identifier = names_to_gallery_identifiers[ name ]
                    
                    with ClientGUIDialogs.DialogInputImportTagOptions( self, name, gallery_identifier ) as ito_dlg:
                        
                        if ito_dlg.ShowModal() == wx.ID_OK:
                            
                            import_tag_options = ito_dlg.GetImportTagOptions()
                            
                            self._import_tag_options.Append( name, ( gallery_identifier, import_tag_options ) )
                            
                        
                    
                
            
        
        def EventDelete( self, event ):
            
            selection = self._import_tag_options.GetSelection()
            
            if selection != wx.NOT_FOUND: self._import_tag_options.Delete( selection )
            
        
        def EventEdit( self, event ):
            
            selection = self._import_tag_options.GetSelection()
            
            if selection != wx.NOT_FOUND:
                
                name = self._import_tag_options.GetString( selection )
                
                ( gallery_identifier, import_tag_options ) = self._import_tag_options.GetClientData( selection )
                
                with ClientGUIDialogs.DialogInputImportTagOptions( self, name, gallery_identifier, import_tag_options ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        import_tag_options = dlg.GetImportTagOptions()
                        
                        self._import_tag_options.SetClientData( selection, ( gallery_identifier, import_tag_options ) )
                        
                    
                
            
        
        def UpdateOptions( self ):
            
            self._new_options.ClearDefaultImportTagOptions()
            
            for ( gallery_identifier, import_tag_options ) in [ self._import_tag_options.GetClientData( i ) for i in range( self._import_tag_options.GetCount() ) ]:
                
                self._new_options.SetDefaultImportTagOptions( gallery_identifier, import_tag_options )
                
            
        
    
    class _FilesAndTrashPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._export_location = wx.DirPickerCtrl( self, style = wx.DIRP_USE_TEXTCTRL )
            
            self._delete_to_recycle_bin = wx.CheckBox( self, label = '' )
            self._exclude_deleted_files = wx.CheckBox( self, label = '' )
            
            self._remove_filtered_files = wx.CheckBox( self, label = '' )
            self._remove_trashed_files = wx.CheckBox( self, label = '' )
            
            self._trash_max_age = ClientGUICommon.NoneableSpinCtrl( self, '', none_phrase = 'no age limit', min = 0, max = 8640 )
            self._trash_max_size = ClientGUICommon.NoneableSpinCtrl( self, '', none_phrase = 'no size limit', min = 0, max = 20480 )
            
            #
            
            if HC.options[ 'export_path' ] is not None:
                
                abs_path = HydrusPaths.ConvertPortablePathToAbsPath( HC.options[ 'export_path' ] )
                
                if abs_path is not None: self._export_location.SetPath( abs_path )
                
            
            self._delete_to_recycle_bin.SetValue( HC.options[ 'delete_to_recycle_bin' ] )
            self._exclude_deleted_files.SetValue( HC.options[ 'exclude_deleted_files' ] )
            self._remove_filtered_files.SetValue( HC.options[ 'remove_filtered_files' ] )
            self._remove_trashed_files.SetValue( HC.options[ 'remove_trashed_files' ] )
            self._trash_max_age.SetValue( HC.options[ 'trash_max_age' ] )
            self._trash_max_size.SetValue( HC.options[ 'trash_max_size' ] )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'Default export directory: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._export_location, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            gridbox.AddF( wx.StaticText( self, label = 'When deleting files or folders, send them to the OS\'s recycle bin: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._delete_to_recycle_bin, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'By default, do not reimport files that have been previously deleted: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._exclude_deleted_files, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Remove files from view when they are filtered: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._remove_filtered_files, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Remove files from view when they are sent to the trash: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._remove_trashed_files, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Number of hours a file can be in the trash before being deleted: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._trash_max_age, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Maximum size of trash (MB): ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._trash_max_size, CC.FLAGS_MIXED )
            
            text = 'If you set the default export directory blank, the client will use \'hydrus_export\' under the current user\'s home directory.'
            
            vbox.AddF( wx.StaticText( self, label = text ), CC.FLAGS_CENTER )
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
            
            self.SetSizer( vbox )
            
        
        def UpdateOptions( self ):
            
            HC.options[ 'export_path' ] = HydrusPaths.ConvertAbsPathToPortablePath( HydrusData.ToUnicode( self._export_location.GetPath() ) )
            
            HC.options[ 'delete_to_recycle_bin' ] = self._delete_to_recycle_bin.GetValue()
            HC.options[ 'exclude_deleted_files' ] = self._exclude_deleted_files.GetValue()
            HC.options[ 'remove_filtered_files' ] = self._remove_filtered_files.GetValue()
            HC.options[ 'remove_trashed_files' ] = self._remove_trashed_files.GetValue()
            HC.options[ 'trash_max_age' ] = self._trash_max_age.GetValue()
            HC.options[ 'trash_max_size' ] = self._trash_max_size.GetValue()
            
        
    
    class _GUIPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._default_gui_session = wx.Choice( self )
            
            self._confirm_client_exit = wx.CheckBox( self )
            self._confirm_trash = wx.CheckBox( self )
            self._confirm_archive = wx.CheckBox( self )
            
            self._always_embed_autocompletes = wx.CheckBox( self )
            
            self._gui_capitalisation = wx.CheckBox( self )
            
            self._hide_preview = wx.CheckBox( self )
            
            self._show_thumbnail_title_banner = wx.CheckBox( self )
            self._show_thumbnail_page = wx.CheckBox( self )
            
            frame_locations_panel = ClientGUICommon.StaticBox( self, 'frame locations' )
            
            self._frame_locations = ClientGUICommon.SaneListCtrl( frame_locations_panel, 200, [ ( 'name', -1 ), ( 'remember size', 90 ), ( 'remember position', 90 ), ( 'last size', 90 ), ( 'last position', 90 ), ( 'default gravity', 90 ), ( 'default position', 90 ), ( 'maximised', 90 ), ( 'fullscreen', 90 ) ] )
            
            self._frame_locations_edit_button = wx.Button( frame_locations_panel, label = 'edit' )
            self._frame_locations_edit_button.Bind( wx.EVT_BUTTON, self.EventEditFrameLocation )
            
            #
            
            self._new_options = HydrusGlobals.client_controller.GetNewOptions()
            
            gui_session_names = HydrusGlobals.client_controller.Read( 'serialisable_names', HydrusSerialisable.SERIALISABLE_TYPE_GUI_SESSION )
            
            if 'last session' not in gui_session_names: gui_session_names.insert( 0, 'last session' )
            
            self._default_gui_session.Append( 'just a blank page', None )
            
            for name in gui_session_names: self._default_gui_session.Append( name, name )
            
            try: self._default_gui_session.SetStringSelection( HC.options[ 'default_gui_session' ] )
            except: self._default_gui_session.SetSelection( 0 )
            
            self._confirm_client_exit.SetValue( HC.options[ 'confirm_client_exit' ] )
            
            self._confirm_trash.SetValue( HC.options[ 'confirm_trash' ] )
            
            self._confirm_archive.SetValue( HC.options[ 'confirm_archive' ] )
            
            self._always_embed_autocompletes.SetValue( HC.options[ 'always_embed_autocompletes' ] )
            
            self._gui_capitalisation.SetValue( HC.options[ 'gui_capitalisation' ] )
            
            remember_tuple = self._new_options.GetFrameLocation( 'manage_tags_dialog' )
            
            self._hide_preview.SetValue( HC.options[ 'hide_preview' ] )
            
            self._show_thumbnail_title_banner.SetValue( self._new_options.GetBoolean( 'show_thumbnail_title_banner' ) )
            
            self._show_thumbnail_page.SetValue( self._new_options.GetBoolean( 'show_thumbnail_page' ) )
            
            for ( name, info ) in self._new_options.GetFrameLocations():
                
                listctrl_list = [ name ] + list( info )
                
                pretty_listctrl_list = self._GetPrettyFrameLocationInfo( listctrl_list )
                
                self._frame_locations.Append( pretty_listctrl_list, listctrl_list )
                
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'Default session on startup:' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._default_gui_session, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Confirm client exit:' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._confirm_client_exit, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Confirm sending files to trash:' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._confirm_trash, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Confirm sending more than one file to archive or inbox:' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._confirm_archive, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Always embed autocomplete dropdown results window:' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._always_embed_autocompletes, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Capitalise gui: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._gui_capitalisation, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Hide the preview window: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._hide_preview, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Show \'title\' banner on thumbnails: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._show_thumbnail_title_banner, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Show volume/chapter/page number on thumbnails: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._show_thumbnail_page, CC.FLAGS_MIXED )
            
            text = 'Here you can override the current and default values for many frame and dialog sizing and positioning variables.'
            text += os.linesep
            text += 'This is an advanced control. If you aren\'t confident of what you are doing here, come back later!'
            
            frame_locations_panel.AddF( wx.StaticText( frame_locations_panel, label = text ), CC.FLAGS_EXPAND_PERPENDICULAR )
            frame_locations_panel.AddF( self._frame_locations, CC.FLAGS_EXPAND_BOTH_WAYS )
            frame_locations_panel.AddF( self._frame_locations_edit_button, CC.FLAGS_LONE_BUTTON )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( frame_locations_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            self.SetSizer( vbox )
            
        
        def _GetPrettyFrameLocationInfo( self, listctrl_list ):
            
            pretty_listctrl_list = []
            
            for item in listctrl_list:
                
                pretty_listctrl_list.append( str( item ) )
                
            
            return pretty_listctrl_list
            
        
        def EventEditFrameLocation( self, event ):
            
            for i in self._frame_locations.GetAllSelected():
                
                listctrl_list = self._frame_locations.GetClientData( i )
                
                title = 'set frame location information'
                
                with ClientGUITopLevelWindows.DialogEdit( self, title ) as dlg:
                    
                    panel = EditFrameLocationPanel( dlg, listctrl_list )
                    
                    dlg.SetPanel( panel )
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        new_listctrl_list = panel.GetValue()
                        pretty_new_listctrl_list = self._GetPrettyFrameLocationInfo( new_listctrl_list )
                        
                        self._frame_locations.UpdateRow( i, pretty_new_listctrl_list, new_listctrl_list )
                        
                    
                
            
        
        def UpdateOptions( self ):
            
            HC.options[ 'default_gui_session' ] = self._default_gui_session.GetStringSelection()
            HC.options[ 'confirm_client_exit' ] = self._confirm_client_exit.GetValue()
            HC.options[ 'confirm_trash' ] = self._confirm_trash.GetValue()
            HC.options[ 'confirm_archive' ] = self._confirm_archive.GetValue()
            HC.options[ 'always_embed_autocompletes' ] = self._always_embed_autocompletes.GetValue()
            HC.options[ 'gui_capitalisation' ] = self._gui_capitalisation.GetValue()
            
            HC.options[ 'hide_preview' ] = self._hide_preview.GetValue()
            
            self._new_options.SetBoolean( 'show_thumbnail_title_banner', self._show_thumbnail_title_banner.GetValue() )
            self._new_options.SetBoolean( 'show_thumbnail_page', self._show_thumbnail_page.GetValue() )
            
            for listctrl_list in self._frame_locations.GetClientData():
                
                ( name, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = listctrl_list
                
                self._new_options.SetFrameLocation( name, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen )
                
            
        
    
    class _MediaPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._new_options = HydrusGlobals.client_controller.GetNewOptions()
            
            self._fit_to_canvas = wx.CheckBox( self, label = '' )
            self._animation_start_position = wx.SpinCtrl( self, min = 0, max = 100 )
            
            self._disable_cv_for_gifs = wx.CheckBox( self, label = '' )
            
            self._mime_media_viewer_panel = ClientGUICommon.StaticBox( self, 'media viewer mime handling' )
            
            self._mime_media_viewer_actions = {}
            
            mimes_in_correct_order = ( HC.IMAGE_JPEG, HC.IMAGE_PNG, HC.IMAGE_GIF, HC.APPLICATION_FLASH, HC.APPLICATION_PDF, HC.VIDEO_FLV, HC.VIDEO_MP4, HC.VIDEO_MKV, HC.VIDEO_WEBM, HC.VIDEO_WMV, HC.AUDIO_MP3, HC.AUDIO_OGG, HC.AUDIO_FLAC, HC.AUDIO_WMA )
            
            for mime in mimes_in_correct_order:
                
                dropdown = ClientGUICommon.BetterChoice( self._mime_media_viewer_panel )
                
                for action in CC.media_viewer_capabilities[ mime ]:
                    
                    dropdown.Append( CC.media_viewer_action_string_lookup[ action ], action )
                    
                
                current_action = HC.options[ 'mime_media_viewer_actions' ][ mime ]
                
                dropdown.SelectClientData( current_action )
                
                self._mime_media_viewer_actions[ mime ] = dropdown
                
            
            #
            
            self._fit_to_canvas.SetValue( HC.options[ 'fit_to_canvas' ] )
            self._animation_start_position.SetValue( int( HC.options[ 'animation_start_position' ] * 100.0 ) )
            self._disable_cv_for_gifs.SetValue( self._new_options.GetBoolean( 'disable_cv_for_gifs' ) )
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            for mime in mimes_in_correct_order:
                
                gridbox.AddF( wx.StaticText( self._mime_media_viewer_panel, label = HC.mime_string_lookup[ mime ] ), CC.FLAGS_MIXED )
                gridbox.AddF( self._mime_media_viewer_actions[ mime ], CC.FLAGS_MIXED )
                
            
            self._mime_media_viewer_panel.AddF( gridbox, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'Zoom smaller media to fit media canvas: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._fit_to_canvas, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Start animations this % in: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._animation_start_position, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Disable OpenCV for gifs: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._disable_cv_for_gifs, CC.FLAGS_MIXED )
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._mime_media_viewer_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def UpdateOptions( self ):
            
            HC.options[ 'fit_to_canvas' ] = self._fit_to_canvas.GetValue()
            HC.options[ 'animation_start_position' ] = float( self._animation_start_position.GetValue() ) / 100.0
            
            mime_media_viewer_actions = {}
            
            for ( mime, dropdown ) in self._mime_media_viewer_actions.items():
                
                mime_media_viewer_actions[ mime ] = dropdown.GetChoice()
                
            
            HC.options[ 'mime_media_viewer_actions' ] = mime_media_viewer_actions
            
            self._new_options.SetBoolean( 'disable_cv_for_gifs', self._disable_cv_for_gifs.GetValue() )
            
        
    
    class _ServerPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._local_port = ClientGUICommon.NoneableSpinCtrl( self, 'local server port', none_phrase = 'do not run local server', min = 1, max = 65535 )
            
            #
            
            self._local_port.SetValue( HC.options[ 'local_port' ] )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( self._local_port, CC.FLAGS_MIXED )
            
            self.SetSizer( vbox )
            
        
        def UpdateOptions( self ):
            
            new_local_port = self._local_port.GetValue()
            
            if new_local_port != HC.options[ 'local_port' ]: HydrusGlobals.client_controller.pub( 'restart_server' )
            
            HC.options[ 'local_port' ] = new_local_port
            
        
    
    class _ShortcutsPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._shortcuts = ClientGUICommon.SaneListCtrl( self, 480, [ ( 'modifier', 120 ), ( 'key', 120 ), ( 'action', -1 ) ], delete_key_callback = self.DeleteShortcuts )
            
            self._shortcuts_add = wx.Button( self, label = 'add' )
            self._shortcuts_add.Bind( wx.EVT_BUTTON, self.EventAdd )
            
            self._shortcuts_edit = wx.Button( self, label = 'edit' )
            self._shortcuts_edit.Bind( wx.EVT_BUTTON, self.EventEdit )
            
            self._shortcuts_delete = wx.Button( self, label = 'delete' )
            self._shortcuts_delete.Bind( wx.EVT_BUTTON, self.EventDelete )
            
            #
            
            for ( modifier, key_dict ) in HC.options[ 'shortcuts' ].items():
                
                for ( key, action ) in key_dict.items():
                    
                    ( pretty_modifier, pretty_key ) = ClientData.ConvertShortcutToPrettyShortcut( modifier, key )
                    
                    pretty_action = action
                    
                    self._shortcuts.Append( ( pretty_modifier, pretty_key, pretty_action ), ( modifier, key, action ) )
                    
                
            
            self._SortListCtrl()
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( wx.StaticText( self, label = 'These shortcuts are global to the main gui! You probably want to stick to function keys or ctrl + something!' ), CC.FLAGS_MIXED )
            vbox.AddF( self._shortcuts, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            hbox.AddF( self._shortcuts_add, CC.FLAGS_BUTTON_SIZER )
            hbox.AddF( self._shortcuts_edit, CC.FLAGS_BUTTON_SIZER )
            hbox.AddF( self._shortcuts_delete, CC.FLAGS_BUTTON_SIZER )
            
            vbox.AddF( hbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def _SortListCtrl( self ): self._shortcuts.SortListItems( 2 )
        
        def DeleteShortcuts( self ):
            
            self._shortcuts.RemoveAllSelected()
            
        
        def EventAdd( self, event ):
            
            with ClientGUIDialogs.DialogInputShortcut( self ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    ( modifier, key, action ) = dlg.GetInfo()
                    
                    ( pretty_modifier, pretty_key ) = ClientData.ConvertShortcutToPrettyShortcut( modifier, key )
                    
                    pretty_action = action
                    
                    self._shortcuts.Append( ( pretty_modifier, pretty_key, pretty_action ), ( modifier, key, action ) )
                    
                    self._SortListCtrl()
                    
                
            
        
        def EventDelete( self, event ):
            
            self.DeleteShortcuts()
            
        
        def EventEdit( self, event ):
            
            indices = self._shortcuts.GetAllSelected()
            
            for index in indices:
                
                ( modifier, key, action ) = self._shortcuts.GetClientData( index )
                
                with ClientGUIDialogs.DialogInputShortcut( self, modifier, key, action ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        ( modifier, key, action ) = dlg.GetInfo()
                        
                        ( pretty_modifier, pretty_key ) = ClientData.ConvertShortcutToPrettyShortcut( modifier, key )
                        
                        pretty_action = action
                        
                        self._shortcuts.UpdateRow( index, ( pretty_modifier, pretty_key, pretty_action ), ( modifier, key, action ) )
                        
                        self._SortListCtrl()
                        
                    
                
            
        
        def UpdateOptions( self ):
            
            shortcuts = {}
            
            shortcuts[ wx.ACCEL_NORMAL ] = {}
            shortcuts[ wx.ACCEL_CTRL ] = {}
            shortcuts[ wx.ACCEL_ALT ] = {}
            shortcuts[ wx.ACCEL_SHIFT ] = {}
            
            for ( modifier, key, action ) in self._shortcuts.GetClientData(): shortcuts[ modifier ][ key ] = action
            
            HC.options[ 'shortcuts' ] = shortcuts
            
        
    
    class _SortCollectPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._default_sort = ClientGUICommon.ChoiceSort( self, sort_by = HC.options[ 'sort_by' ] )
            
            self._default_collect = ClientGUICommon.CheckboxCollect( self )
            
            self._sort_by = wx.ListBox( self )
            self._sort_by.Bind( wx.EVT_LEFT_DCLICK, self.EventRemoveSortBy )
            
            self._new_sort_by = wx.TextCtrl( self, style = wx.TE_PROCESS_ENTER )
            self._new_sort_by.Bind( wx.EVT_KEY_DOWN, self.EventKeyDownSortBy )
            
            #
            
            for ( sort_by_type, sort_by ) in HC.options[ 'sort_by' ]: self._sort_by.Append( '-'.join( sort_by ), sort_by )
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'default sort: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._default_sort, CC.FLAGS_EXPAND_BOTH_WAYS )
            gridbox.AddF( wx.StaticText( self, label = 'default collect: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._default_collect, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            sort_by_text = 'You can manage new namespace sorting schemes here.'
            sort_by_text += os.linesep
            sort_by_text += 'The client will sort media by comparing their namespaces, moving from left to right until an inequality is found.'
            sort_by_text += os.linesep
            sort_by_text += 'Any changes will be shown in the sort-by dropdowns of any new pages you open.'
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            vbox.AddF( wx.StaticText( self, label = sort_by_text ), CC.FLAGS_MIXED )
            vbox.AddF( self._sort_by, CC.FLAGS_EXPAND_BOTH_WAYS )
            vbox.AddF( self._new_sort_by, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def EventKeyDownSortBy( self, event ):
            
            if event.KeyCode in ( wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER ):
                
                sort_by_string = self._new_sort_by.GetValue()
                
                if sort_by_string != '':
                    
                    try: sort_by = sort_by_string.split( '-' )
                    except:
                        
                        wx.MessageBox( 'Could not parse that sort by string!' )
                        
                        return
                        
                    
                    self._sort_by.Append( sort_by_string, sort_by )
                    
                    self._new_sort_by.SetValue( '' )
                    
                
            else: event.Skip()
            
        
        def EventRemoveSortBy( self, event ):
            
            selection = self._sort_by.GetSelection()
            
            if selection != wx.NOT_FOUND: self._sort_by.Delete( selection )
            
        
        def UpdateOptions( self ):
            
            HC.options[ 'default_sort' ] = self._default_sort.GetSelection() 
            HC.options[ 'default_collect' ] = self._default_collect.GetChoice()
            
            sort_by_choices = []
            
            for sort_by in [ self._sort_by.GetClientData( i ) for i in range( self._sort_by.GetCount() ) ]: sort_by_choices.append( ( 'namespaces', sort_by ) )
            
            HC.options[ 'sort_by' ] = sort_by_choices
            
        
    
    class _SoundPanel( wx.Panel ):
        
        def __init__( self, parent ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._play_dumper_noises = wx.CheckBox( self, label = 'play success/fail noises when dumping' )
            
            #
            
            self._play_dumper_noises.SetValue( HC.options[ 'play_dumper_noises' ] )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( self._play_dumper_noises, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def UpdateOptions( self ):
            
            HC.options[ 'play_dumper_noises' ] = self._play_dumper_noises.GetValue()
            
        
    
    class _SpeedAndMemoryPanel( wx.Panel ):
        
        def __init__( self, parent, new_options ):
            
            wx.Panel.__init__( self, parent )
            
            self._new_options = new_options
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._disk_cache_init_period = ClientGUICommon.NoneableSpinCtrl( self, 'max disk cache init period', none_phrase = 'do not run', min = 1, max = 120 )
            self._disk_cache_init_period.SetToolTipString( 'When the client boots, it can speed up operation by reading the front of the database into memory. This sets the max number of seconds it can spend doing that.' )
            
            self._disk_cache_maintenance_mb = ClientGUICommon.NoneableSpinCtrl( self, 'disk cache maintenance (MB)', none_phrase = 'do not keep db cached', min = 32, max = 65536 )
            self._disk_cache_maintenance_mb.SetToolTipString( 'The client can regularly check the front of its database is cached in memory. This represents how many megabytes it will ensure are cached.' )
            
            self._thumbnail_width = wx.SpinCtrl( self, min = 20, max = 200 )
            self._thumbnail_width.Bind( wx.EVT_SPINCTRL, self.EventThumbnailsUpdate )
            
            self._thumbnail_height = wx.SpinCtrl( self, min = 20, max = 200 )
            self._thumbnail_height.Bind( wx.EVT_SPINCTRL, self.EventThumbnailsUpdate )
            
            self._thumbnail_cache_size = wx.SpinCtrl( self, min = 5, max = 3000 )
            self._thumbnail_cache_size.Bind( wx.EVT_SPINCTRL, self.EventThumbnailsUpdate )
            
            self._estimated_number_thumbnails = wx.StaticText( self, label = '' )
            
            self._preview_cache_size = wx.SpinCtrl( self, min = 5, max = 3000 )
            self._preview_cache_size.Bind( wx.EVT_SPINCTRL, self.EventPreviewsUpdate )
            
            self._estimated_number_previews = wx.StaticText( self, label = '' )
            
            self._fullscreen_cache_size = wx.SpinCtrl( self, min = 25, max = 3000 )
            self._fullscreen_cache_size.Bind( wx.EVT_SPINCTRL, self.EventFullscreensUpdate )
            
            self._estimated_number_fullscreens = wx.StaticText( self, label = '' )
            
            self._forced_search_limit = ClientGUICommon.NoneableSpinCtrl( self, '', min = 1, max = 100000 )
            
            self._num_autocomplete_chars = wx.SpinCtrl( self, min = 1, max = 100 )
            self._num_autocomplete_chars.SetToolTipString( 'how many characters you enter before the gui fetches autocomplete results from the db. (otherwise, it will only fetch exact matches)' + os.linesep + 'increase this if you find autocomplete results are slow' )
            
            self._fetch_ac_results_automatically = wx.CheckBox( self )
            self._fetch_ac_results_automatically.Bind( wx.EVT_CHECKBOX, self.EventFetchAuto )
            
            self._autocomplete_long_wait = wx.SpinCtrl( self, min = 0, max = 10000 )
            self._autocomplete_long_wait.SetToolTipString( 'how long the gui will typically wait, after you enter a character, before it queries the db with what you have entered so far' )
            
            self._autocomplete_short_wait_chars = wx.SpinCtrl( self, min = 1, max = 100 )
            self._autocomplete_short_wait_chars.SetToolTipString( 'how many characters you enter before the gui starts waiting the short time before querying the db' )
            
            self._autocomplete_short_wait = wx.SpinCtrl( self, min = 0, max = 10000 )
            self._autocomplete_short_wait.SetToolTipString( 'how long the gui will typically wait, after you enter a lot of characters, before it queries the db with what you have entered so far' )
            
            #
            
            self._disk_cache_init_period.SetValue( self._new_options.GetNoneableInteger( 'disk_cache_init_period' ) )
            self._disk_cache_maintenance_mb.SetValue( self._new_options.GetNoneableInteger( 'disk_cache_maintenance_mb' ) )
            
            ( thumbnail_width, thumbnail_height ) = HC.options[ 'thumbnail_dimensions' ]
            
            self._thumbnail_width.SetValue( thumbnail_width )
            
            self._thumbnail_height.SetValue( thumbnail_height )
            
            self._thumbnail_cache_size.SetValue( int( HC.options[ 'thumbnail_cache_size' ] / 1048576 ) )
            
            self._preview_cache_size.SetValue( int( HC.options[ 'preview_cache_size' ] / 1048576 ) )
            
            self._fullscreen_cache_size.SetValue( int( HC.options[ 'fullscreen_cache_size' ] / 1048576 ) )
            
            self._forced_search_limit.SetValue( self._new_options.GetNoneableInteger( 'forced_search_limit' ) )
            
            self._num_autocomplete_chars.SetValue( HC.options[ 'num_autocomplete_chars' ] )
            
            self._fetch_ac_results_automatically.SetValue( HC.options[ 'fetch_ac_results_automatically' ] )
            
            ( char_limit, long_wait, short_wait ) = HC.options[ 'ac_timings' ]
            
            self._autocomplete_long_wait.SetValue( long_wait )
            
            self._autocomplete_short_wait_chars.SetValue( char_limit )
            
            self._autocomplete_short_wait.SetValue( short_wait )
            
            #
            
            thumbnails_sizer = wx.BoxSizer( wx.HORIZONTAL )
            
            thumbnails_sizer.AddF( self._thumbnail_cache_size, CC.FLAGS_MIXED )
            thumbnails_sizer.AddF( self._estimated_number_thumbnails, CC.FLAGS_MIXED )
            
            previews_sizer = wx.BoxSizer( wx.HORIZONTAL )
            
            previews_sizer.AddF( self._preview_cache_size, CC.FLAGS_MIXED )
            previews_sizer.AddF( self._estimated_number_previews, CC.FLAGS_MIXED )
            
            fullscreens_sizer = wx.BoxSizer( wx.HORIZONTAL )
            
            fullscreens_sizer.AddF( self._fullscreen_cache_size, CC.FLAGS_MIXED )
            fullscreens_sizer.AddF( self._estimated_number_fullscreens, CC.FLAGS_MIXED )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( self._disk_cache_init_period, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( self._disk_cache_maintenance_mb, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'Thumbnail width: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._thumbnail_width, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Thumbnail height: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._thumbnail_height, CC.FLAGS_MIXED )
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'MB memory reserved for thumbnail cache: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( thumbnails_sizer, CC.FLAGS_NONE )
            
            gridbox.AddF( wx.StaticText( self, label = 'MB memory reserved for preview cache: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( previews_sizer, CC.FLAGS_NONE )
            
            gridbox.AddF( wx.StaticText( self, label = 'MB memory reserved for media viewer cache: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( fullscreens_sizer, CC.FLAGS_NONE )
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'Forced system:limit for all searches: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._forced_search_limit, CC.FLAGS_NONE )
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            text = 'If you disable automatic autocomplete results fetching, use Ctrl+Space to fetch results manually.'
            
            vbox.AddF( wx.StaticText( self, label = text ), CC.FLAGS_EXPAND_PERPENDICULAR )
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'Automatically fetch autocomplete results after a short delay: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._fetch_ac_results_automatically, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Autocomplete long wait character threshold: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._num_autocomplete_chars, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Autocomplete long wait (ms): ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._autocomplete_long_wait, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Autocomplete short wait character threshold: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._autocomplete_short_wait_chars, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Autocomplete short wait (ms): ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._autocomplete_short_wait, CC.FLAGS_MIXED )
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
            #
            
            self.EventFetchAuto( None )
            self.EventFullscreensUpdate( None )
            self.EventPreviewsUpdate( None )
            self.EventThumbnailsUpdate( None )
            
            wx.CallAfter( self.Layout ) # draws the static texts correctly
            
        
        def EventFetchAuto( self, event ):
            
            if self._fetch_ac_results_automatically.GetValue() == True:
                
                self._autocomplete_long_wait.Enable()
                self._autocomplete_short_wait_chars.Enable()
                self._autocomplete_short_wait.Enable()
                
            else:
                
                self._autocomplete_long_wait.Disable()
                self._autocomplete_short_wait_chars.Disable()
                self._autocomplete_short_wait.Disable()
                
            
        
        def EventFullscreensUpdate( self, event ):
            
            ( width, height ) = wx.GetDisplaySize()
            
            estimated_bytes_per_fullscreen = 3 * width * height
            
            self._estimated_number_fullscreens.SetLabelText( '(about ' + HydrusData.ConvertIntToPrettyString( ( self._fullscreen_cache_size.GetValue() * 1048576 ) / estimated_bytes_per_fullscreen ) + '-' + HydrusData.ConvertIntToPrettyString( ( self._fullscreen_cache_size.GetValue() * 1048576 ) / ( estimated_bytes_per_fullscreen / 4 ) ) + ' images)' )
            
        
        def EventPreviewsUpdate( self, event ):
            
            estimated_bytes_per_preview = 3 * 400 * 400
            
            self._estimated_number_previews.SetLabelText( '(about ' + HydrusData.ConvertIntToPrettyString( ( self._preview_cache_size.GetValue() * 1048576 ) / estimated_bytes_per_preview ) + ' previews)' )
            
        
        def EventThumbnailsUpdate( self, event ):
            
            estimated_bytes_per_thumb = 3 * self._thumbnail_height.GetValue() * self._thumbnail_width.GetValue()
            
            self._estimated_number_thumbnails.SetLabelText( '(about ' + HydrusData.ConvertIntToPrettyString( ( self._thumbnail_cache_size.GetValue() * 1048576 ) / estimated_bytes_per_thumb ) + ' thumbnails)' )
            
        
        def UpdateOptions( self ):
            
            self._new_options.SetNoneableInteger( 'disk_cache_init_period', self._disk_cache_init_period.GetValue() )
            self._new_options.SetNoneableInteger( 'disk_cache_maintenance_mb', self._disk_cache_maintenance_mb.GetValue() )
            
            new_thumbnail_dimensions = [ self._thumbnail_width.GetValue(), self._thumbnail_height.GetValue() ]
            
            HC.options[ 'thumbnail_dimensions' ] = new_thumbnail_dimensions
            
            HC.options[ 'thumbnail_cache_size' ] = self._thumbnail_cache_size.GetValue() * 1048576
            HC.options[ 'preview_cache_size' ] = self._preview_cache_size.GetValue() * 1048576
            HC.options[ 'fullscreen_cache_size' ] = self._fullscreen_cache_size.GetValue() * 1048576
            
            self._new_options.SetNoneableInteger( 'forced_search_limit', self._forced_search_limit.GetValue() )
            
            HC.options[ 'num_autocomplete_chars' ] = self._num_autocomplete_chars.GetValue()
            
            HC.options[ 'fetch_ac_results_automatically' ] = self._fetch_ac_results_automatically.GetValue()
            
            long_wait = self._autocomplete_long_wait.GetValue()
            
            char_limit = self._autocomplete_short_wait_chars.GetValue()
            
            short_wait = self._autocomplete_short_wait.GetValue()
            
            HC.options[ 'ac_timings' ] = ( char_limit, long_wait, short_wait )
            
        
    
    class _TagsPanel( wx.Panel ):
        
        def __init__( self, parent, new_options ):
            
            wx.Panel.__init__( self, parent )
            
            self._new_options = new_options
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            self._default_tag_sort = wx.Choice( self )
            
            self._default_tag_sort.Append( 'lexicographic (a-z)', CC.SORT_BY_LEXICOGRAPHIC_ASC )
            self._default_tag_sort.Append( 'lexicographic (z-a)', CC.SORT_BY_LEXICOGRAPHIC_DESC )
            self._default_tag_sort.Append( 'lexicographic (a-z) (grouped by namespace)', CC.SORT_BY_LEXICOGRAPHIC_NAMESPACE_ASC )
            self._default_tag_sort.Append( 'lexicographic (z-a) (grouped by namespace)', CC.SORT_BY_LEXICOGRAPHIC_NAMESPACE_DESC )
            self._default_tag_sort.Append( 'incidence (desc)', CC.SORT_BY_INCIDENCE_DESC )
            self._default_tag_sort.Append( 'incidence (asc)', CC.SORT_BY_INCIDENCE_ASC )
            
            self._default_tag_repository = ClientGUICommon.BetterChoice( self )
            
            self._show_all_tags_in_autocomplete = wx.CheckBox( self )
            
            self._apply_all_parents_to_all_services = wx.CheckBox( self )
            
            suggested_tags_panel = ClientGUICommon.StaticBox( self, 'suggested tags' )
            
            self._suggested_tags_width = ClientGUICommon.NoneableSpinCtrl( suggested_tags_panel, 'width of suggested tags control', min = 20, none_phrase = 'width of longest tag', unit = 'pixels' )
            
            suggested_tags_favourites_panel = ClientGUICommon.StaticBox( suggested_tags_panel, 'favourites' )
            
            suggested_tags_favourites_panel.SetMinSize( ( 400, -1 ) )
            
            self._suggested_favourites_services = ClientGUICommon.BetterChoice( suggested_tags_favourites_panel )
            
            self._suggested_favourites_services.Append( CC.LOCAL_TAG_SERVICE_KEY, CC.LOCAL_TAG_SERVICE_KEY )
            
            tag_services = HydrusGlobals.client_controller.GetServicesManager().GetServices( ( HC.TAG_REPOSITORY, ) )
            
            for tag_service in tag_services:
                
                self._suggested_favourites_services.Append( tag_service.GetName(), tag_service.GetServiceKey() )
                
            
            self._suggested_favourites = ClientGUICommon.ListBoxTagsStringsAddRemove( suggested_tags_favourites_panel )
            
            self._current_suggested_favourites_service = None
            
            self._suggested_favourites_dict = {}
            
            expand_parents = False
            
            self._suggested_favourites_input = ClientGUICommon.AutoCompleteDropdownTagsWrite( suggested_tags_favourites_panel, self._suggested_favourites.AddTags, expand_parents, CC.LOCAL_FILE_SERVICE_KEY, CC.LOCAL_TAG_SERVICE_KEY )
            
            #
            
            if HC.options[ 'default_tag_sort' ] == CC.SORT_BY_LEXICOGRAPHIC_ASC: self._default_tag_sort.Select( 0 )
            elif HC.options[ 'default_tag_sort' ] == CC.SORT_BY_LEXICOGRAPHIC_DESC: self._default_tag_sort.Select( 1 )
            elif HC.options[ 'default_tag_sort' ] == CC.SORT_BY_LEXICOGRAPHIC_NAMESPACE_ASC: self._default_tag_sort.Select( 2 )
            elif HC.options[ 'default_tag_sort' ] == CC.SORT_BY_LEXICOGRAPHIC_NAMESPACE_DESC: self._default_tag_sort.Select( 3 )
            elif HC.options[ 'default_tag_sort' ] == CC.SORT_BY_INCIDENCE_DESC: self._default_tag_sort.Select( 4 )
            elif HC.options[ 'default_tag_sort' ] == CC.SORT_BY_INCIDENCE_ASC: self._default_tag_sort.Select( 5 )
            
            services = HydrusGlobals.client_controller.GetServicesManager().GetServices( HC.TAG_SERVICES )
            
            for service in services: self._default_tag_repository.Append( service.GetName(), service.GetServiceKey() )
            
            default_tag_repository_key = HC.options[ 'default_tag_repository' ]
            
            self._default_tag_repository.SelectClientData( default_tag_repository_key )
            
            self._show_all_tags_in_autocomplete.SetValue( HC.options[ 'show_all_tags_in_autocomplete' ] )
            
            self._apply_all_parents_to_all_services.SetValue( self._new_options.GetBoolean( 'apply_all_parents_to_all_services' ) )
            
            self._suggested_tags_width.SetValue( self._new_options.GetNoneableInteger( 'suggested_tags_width' ) )
            
            self._suggested_favourites_services.SelectClientData( CC.LOCAL_TAG_SERVICE_KEY )
            
            #
            
            gridbox = wx.FlexGridSizer( 0, 2 )
            
            gridbox.AddGrowableCol( 1, 1 )
            
            gridbox.AddF( wx.StaticText( self, label = 'Default tag service in manage tag dialogs:' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._default_tag_repository, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Default tag sort:' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._default_tag_sort, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'By default, search non-local tags in write-autocomplete: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._show_all_tags_in_autocomplete, CC.FLAGS_MIXED )
            
            gridbox.AddF( wx.StaticText( self, label = 'Apply all parents to all services: ' ), CC.FLAGS_MIXED )
            gridbox.AddF( self._apply_all_parents_to_all_services, CC.FLAGS_MIXED )
            
            suggested_tags_favourites_panel.AddF( self._suggested_favourites_services, CC.FLAGS_EXPAND_PERPENDICULAR )
            suggested_tags_favourites_panel.AddF( self._suggested_favourites, CC.FLAGS_EXPAND_BOTH_WAYS )
            suggested_tags_favourites_panel.AddF( self._suggested_favourites_input, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            suggested_tags_panel.AddF( self._suggested_tags_width, CC.FLAGS_EXPAND_PERPENDICULAR )
            suggested_tags_panel.AddF( suggested_tags_favourites_panel, CC.FLAGS_EXPAND_SIZER_DEPTH_ONLY )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( suggested_tags_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            self.SetSizer( vbox )
            
            #
            
            self._suggested_favourites_services.Bind( wx.EVT_CHOICE, self.EventSuggestedFavouritesService )
            
            self.EventSuggestedFavouritesService( None )
            
        
        def _SaveCurrentSuggestedFavourites( self ):
            
            if self._current_suggested_favourites_service is not None:
                
                self._suggested_favourites_dict[ self._current_suggested_favourites_service ] = self._suggested_favourites.GetTags()
                
            
        
        def EventSuggestedFavouritesService( self, event ):
            
            self._SaveCurrentSuggestedFavourites()
            
            self._current_suggested_favourites_service = self._suggested_favourites_services.GetChoice()
            
            if self._current_suggested_favourites_service in self._suggested_favourites_dict:
                
                favourites = self._suggested_favourites_dict[ self._current_suggested_favourites_service ]
                
            else:
                
                favourites = self._new_options.GetSuggestedTagsFavourites( self._current_suggested_favourites_service )
                
            
            self._suggested_favourites.SetTags( favourites )
            
            self._suggested_favourites_input.SetTagService( self._current_suggested_favourites_service )
            
        
        def UpdateOptions( self ):
            
            HC.options[ 'default_tag_repository' ] = self._default_tag_repository.GetChoice()
            HC.options[ 'default_tag_sort' ] = self._default_tag_sort.GetClientData( self._default_tag_sort.GetSelection() )
            HC.options[ 'show_all_tags_in_autocomplete' ] = self._show_all_tags_in_autocomplete.GetValue()
            
            self._new_options.SetNoneableInteger( 'suggested_tags_width', self._suggested_tags_width.GetValue() )
            
            self._new_options.SetBoolean( 'apply_all_parents_to_all_services', self._apply_all_parents_to_all_services.GetValue() )
            
            self._SaveCurrentSuggestedFavourites()
            
            for ( service_key, favourites ) in self._suggested_favourites_dict.items():
                
                self._new_options.SetSuggestedTagsFavourites( service_key, favourites )
                
            
        
    
    def CommitChanges( self ):
        
        for page in self._listbook.GetActivePages():
            
            page.UpdateOptions()
            
        
        try:
            
            HydrusGlobals.client_controller.WriteSynchronous( 'save_options', HC.options )
            
            HydrusGlobals.client_controller.WriteSynchronous( 'serialisable', self._new_options )
            
        except:
            
            wx.MessageBox( traceback.format_exc() )
            
        
    
class ManageTagsPanel( ManagePanel ):
    
    def __init__( self, parent, file_service_key, media, immediate_commit = False, canvas_key = None ):
        
        ManagePanel.__init__( self, parent )
        
        self._file_service_key = file_service_key
        
        self._immediate_commit = immediate_commit
        self._canvas_key = canvas_key
        
        media = ClientMedia.FlattenMedia( media )
        
        self._current_media = [ m.Duplicate() for m in media ]
        
        self._hashes = set()
        
        for m in self._current_media:
            
            self._hashes.update( m.GetHashes() )
            
        
        self._tag_repositories = ClientGUICommon.ListBook( self )
        self._tag_repositories.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.EventServiceChanged )
        
        #
        
        services = HydrusGlobals.client_controller.GetServicesManager().GetServices( HC.TAG_SERVICES )
        
        for service in services:
            
            service_key = service.GetServiceKey()
            name = service.GetName()
            
            page = self._Panel( self._tag_repositories, self._file_service_key, service.GetServiceKey(), self._current_media, self._immediate_commit )
            
            self._tag_repositories.AddPage( name, service_key, page )
            
        
        default_tag_repository_key = HC.options[ 'default_tag_repository' ]
        
        self._tag_repositories.Select( default_tag_repository_key )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.AddF( self._tag_repositories, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        self.Bind( wx.EVT_MENU, self.EventMenu )
        self.Bind( wx.EVT_CHAR_HOOK, self.EventCharHook )
        
        self.RefreshAcceleratorTable()
        
        if self._canvas_key is not None:
            
            HydrusGlobals.client_controller.sub( self, 'CanvasHasNewMedia', 'canvas_new_display_media' )
            
        
    
    def _SetSearchFocus( self ):
        
        page = self._tag_repositories.GetCurrentPage()
        
        page.SetTagBoxFocus()
        
    
    def CanvasHasNewMedia( self, canvas_key, new_media_singleton ):
        
        if canvas_key == self._canvas_key:
            
            self._current_media = ( new_media_singleton.Duplicate(), )
            
            for page in self._tag_repositories.GetActivePages():
                
                page.SetMedia( self._current_media )
                
            
        
    
    def CommitChanges( self ):
        
        service_keys_to_content_updates = {}
        
        for page in self._tag_repositories.GetActivePages():
            
            ( service_key, content_updates ) = page.GetContentUpdates()
            
            if len( content_updates ) > 0:
                
                service_keys_to_content_updates[ service_key ] = content_updates
                
            
        
        if len( service_keys_to_content_updates ) > 0:
            
            HydrusGlobals.client_controller.WriteSynchronous( 'content_updates', service_keys_to_content_updates )
            
        
    
    def EventCharHook( self, event ):
        
        if not HC.PLATFORM_LINUX:
            
            # If I let this go uncaught, it propagates to the media viewer above, so an Enter or a '+' closes the window or zooms in!
            # The DoAllowNextEvent tells wx to gen regular key_down/char events so our text box gets them like normal, despite catching the event here
            
            event.DoAllowNextEvent()
            
        else:
            
            # Top jej, the events weren't being generated after all in Linux, so here's a possibly borked patch for that:
            
            HydrusGlobals.do_not_catch_char_hook = True
            
            event.Skip()
            
        
    
    def EventMenu( self, event ):
        
        action = ClientCaches.MENU_EVENT_ID_TO_ACTION_CACHE.GetAction( event.GetId() )
        
        if action is not None:
            
            ( command, data ) = action
            
            if command == 'manage_tags':
                
                wx.PostEvent( self.GetParent(), wx.CommandEvent( commandType = wx.wxEVT_COMMAND_MENU_SELECTED, winid = ClientCaches.MENU_EVENT_ID_TO_ACTION_CACHE.GetTemporaryId( 'ok' ) ) )
                
            elif command == 'set_search_focus':
                
                self._SetSearchFocus()
                
            elif command == 'canvas_show_next':
                
                if self._canvas_key is not None:
                    
                    HydrusGlobals.client_controller.pub( 'canvas_show_next', self._canvas_key )
                    
                
            elif command == 'canvas_show_previous':
                
                if self._canvas_key is not None:
                    
                    HydrusGlobals.client_controller.pub( 'canvas_show_previous', self._canvas_key )
                    
                
            else:
                
                event.Skip()
                
            
        
    
    def EventServiceChanged( self, event ):
        
        page = self._tag_repositories.GetCurrentPage()
        
        wx.CallAfter( page.SetTagBoxFocus )
        
    
    def RefreshAcceleratorTable( self ):
        
        interested_actions = [ 'manage_tags', 'set_search_focus' ]
        
        entries = []
        
        for ( modifier, key_dict ) in HC.options[ 'shortcuts' ].items():
            
            entries.extend( [ ( modifier, key, ClientCaches.MENU_EVENT_ID_TO_ACTION_CACHE.GetPermanentId( action ) ) for ( key, action ) in key_dict.items() if action in interested_actions ] )
            
        
        self.SetAcceleratorTable( wx.AcceleratorTable( entries ) )
        
    
    class _Panel( wx.Panel ):
        
        def __init__( self, parent, file_service_key, tag_service_key, media, immediate_commit ):
            
            wx.Panel.__init__( self, parent )
            
            self._file_service_key = file_service_key
            self._tag_service_key = tag_service_key
            self._immediate_commit = immediate_commit
            
            self._content_updates = []
            
            self._i_am_local_tag_service = self._tag_service_key == CC.LOCAL_TAG_SERVICE_KEY
            
            if not self._i_am_local_tag_service:
                
                service = HydrusGlobals.client_controller.GetServicesManager().GetService( tag_service_key )
                
                try: self._account = service.GetInfo( 'account' )
                except: self._account = HydrusData.GetUnknownAccount()
                
            
            self._tags_box_sorter = ClientGUICommon.StaticBoxSorterForListBoxTags( self, 'tags' )
            
            self._tags_box = ClientGUICommon.ListBoxTagsSelectionTagsDialog( self._tags_box_sorter, self.AddTags )
            
            self._tags_box_sorter.SetTagsBox( self._tags_box )
            
            self._new_options = HydrusGlobals.client_controller.GetNewOptions()
            
            self._collapse_siblings_checkbox = wx.CheckBox( self._tags_box_sorter, label = 'auto-replace entered siblings' )
            self._collapse_siblings_checkbox.SetValue( self._new_options.GetBoolean( 'replace_siblings_on_manage_tags' ) )
            self._collapse_siblings_checkbox.Bind( wx.EVT_CHECKBOX, self.EventCheckCollapseSiblings )
            
            self._show_deleted_checkbox = wx.CheckBox( self._tags_box_sorter, label = 'show deleted' )
            self._show_deleted_checkbox.Bind( wx.EVT_CHECKBOX, self.EventShowDeleted )
            
            self._tags_box_sorter.AddF( self._collapse_siblings_checkbox, CC.FLAGS_LONE_BUTTON )
            self._tags_box_sorter.AddF( self._show_deleted_checkbox, CC.FLAGS_LONE_BUTTON )
            
            expand_parents = True
            
            self._add_tag_box = ClientGUICommon.AutoCompleteDropdownTagsWrite( self, self.EnterTags, expand_parents, self._file_service_key, self._tag_service_key, null_entry_callable = self.Ok )
            
            self._advanced_content_update_button = wx.Button( self, label = 'advanced operation' )
            self._advanced_content_update_button.Bind( wx.EVT_BUTTON, self.EventAdvancedContentUpdate )
            
            self._modify_mappers = wx.Button( self, label = 'modify mappers' )
            self._modify_mappers.Bind( wx.EVT_BUTTON, self.EventModify )
            
            self._copy_tags = wx.Button( self, label = 'copy tags' )
            self._copy_tags.Bind( wx.EVT_BUTTON, self.EventCopyTags )
            
            self._paste_tags = wx.Button( self, label = 'paste tags' )
            self._paste_tags.Bind( wx.EVT_BUTTON, self.EventPasteTags )
            
            if self._i_am_local_tag_service:
                
                text = 'remove all tags'
                
            else:
                
                text = 'petition all tags'
                
            
            self._remove_tags = wx.Button( self, label = text )
            self._remove_tags.Bind( wx.EVT_BUTTON, self.EventRemoveTags )
            
            self._tags_box.ChangeTagService( self._tag_service_key )
            
            self.SetMedia( media )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            if self._i_am_local_tag_service:
                
                self._modify_mappers.Hide()
                
            else:
                
                if not self._account.HasPermission( HC.MANAGE_USERS ):
                    
                    self._modify_mappers.Hide()
                    
                
            
            copy_paste_hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            copy_paste_hbox.AddF( self._copy_tags, CC.FLAGS_MIXED )
            copy_paste_hbox.AddF( self._paste_tags, CC.FLAGS_MIXED )
            
            advanced_hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            advanced_hbox.AddF( self._remove_tags, CC.FLAGS_MIXED )
            advanced_hbox.AddF( self._advanced_content_update_button, CC.FLAGS_MIXED )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.AddF( self._tags_box_sorter, CC.FLAGS_EXPAND_BOTH_WAYS )
            vbox.AddF( self._add_tag_box, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.AddF( copy_paste_hbox, CC.FLAGS_BUTTON_SIZER )
            vbox.AddF( advanced_hbox, CC.FLAGS_BUTTON_SIZER )
            vbox.AddF( self._modify_mappers, CC.FLAGS_LONE_BUTTON )
            
            #
            
            hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            favourites = self._new_options.GetSuggestedTagsFavourites( tag_service_key )
            
            if len( favourites ) > 0:
                
                suggested_tags = ClientGUICommon.ListBoxTagsSuggestions( self, self.AddTags )
                
                suggested_tags.SetTags( favourites )
                
                hbox.AddF( suggested_tags, CC.FLAGS_EXPAND_PERPENDICULAR )
                
            
            hbox.AddF( vbox, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
            
            #
            
            self.SetSizer( hbox )
            
        
        def _AddTags( self, tags, only_add = False, only_remove = False, forced_reason = None ):
            
            if not self._i_am_local_tag_service and self._account.HasPermission( HC.RESOLVE_PETITIONS ):
                
                forced_reason = 'admin'
                
            
            tag_managers = [ m.GetTagsManager() for m in self._media ]
            
            num_files = len( self._media )
            
            sets_of_choices = []
            
            potential_num_reasons_needed = 0
            
            for tag in tags:
                
                num_current = len( [ 1 for tag_manager in tag_managers if tag in tag_manager.GetCurrent( self._tag_service_key ) ] )
                
                choices = []
                
                if self._i_am_local_tag_service:
                    
                    if not only_remove:
                        
                        if num_current < num_files:
                            
                            choices.append( ( 'add ' + tag + ' to ' + HydrusData.ConvertIntToPrettyString( num_files - num_current ) + ' files', ( HC.CONTENT_UPDATE_ADD, tag ) ) )
                            
                        
                    
                    if not only_add:
                        
                        if num_current > 0:
                            
                            choices.append( ( 'delete ' + tag + ' from ' + HydrusData.ConvertIntToPrettyString( num_current ) + ' files', ( HC.CONTENT_UPDATE_DELETE, tag ) ) )
                            
                        
                    
                else:
                    
                    num_pending = len( [ 1 for tag_manager in tag_managers if tag in tag_manager.GetPending( self._tag_service_key ) ] )
                    num_petitioned = len( [ 1 for tag_manager in tag_managers if tag in tag_manager.GetPetitioned( self._tag_service_key ) ] )
                    
                    if not only_remove:
                        
                        if num_current + num_pending < num_files: choices.append( ( 'pend ' + tag + ' to ' + HydrusData.ConvertIntToPrettyString( num_files - ( num_current + num_pending ) ) + ' files', ( HC.CONTENT_UPDATE_PEND, tag ) ) )
                        
                    
                    if not only_add:
                        
                        if num_current > num_petitioned and not only_add:
                            
                            choices.append( ( 'petition ' + tag + ' from ' + HydrusData.ConvertIntToPrettyString( num_current - num_petitioned ) + ' files', ( HC.CONTENT_UPDATE_PETITION, tag ) ) )
                            
                            potential_num_reasons_needed += 1
                            
                        
                        if num_pending > 0 and not only_add:
                            
                            choices.append( ( 'rescind pending ' + tag + ' from ' + HydrusData.ConvertIntToPrettyString( num_pending ) + ' files', ( HC.CONTENT_UPDATE_RESCIND_PEND, tag ) ) )
                            
                        
                    
                    if not only_remove:
                        
                        if num_petitioned > 0:
                            
                            choices.append( ( 'rescind petitioned ' + tag + ' from ' + HydrusData.ConvertIntToPrettyString( num_petitioned ) + ' files', ( HC.CONTENT_UPDATE_RESCIND_PETITION, tag ) ) )
                            
                        
                    
                
                if len( choices ) == 0:
                    
                    continue
                    
                
                sets_of_choices.append( choices )
                
            
            if forced_reason is None and potential_num_reasons_needed > 1:
                
                no_user_choices = True not in ( len( choices ) > 1 for choices in sets_of_choices )
                
                if no_user_choices:
                    
                    message = 'You are about to petition more than one tag.'
                    
                else:
                    
                    message = 'You might be about to petition more than one tag.'
                    
                
                message += os.linesep * 2
                message += 'To save you time, would you like to use the same reason for all the petitions?'
                
                with ClientGUIDialogs.DialogYesNo( self, message, title = 'Many petitions found' ) as yn_dlg:
                    
                    if yn_dlg.ShowModal() == wx.ID_YES:
                        
                        message = 'Please enter your common petition reason here:'
                        
                        with ClientGUIDialogs.DialogTextEntry( self, message ) as text_dlg:
                            
                            if text_dlg.ShowModal() == wx.ID_OK:
                                
                                forced_reason = text_dlg.GetValue()
                                
                            
                        
                    
                
            
            forced_choice_actions = []
            
            for choices in sets_of_choices:
                
                always_do = False
                
                if len( choices ) == 1:
                    
                    [ ( text_gumpf, choice ) ] = choices
                    
                else:
                    
                    choice = None
                    
                    for forced_choice_action in forced_choice_actions:
                        
                        for possible_choice in choices:
                            
                            ( text_gumpf, ( choice_action, choice_tag ) ) = possible_choice
                            
                            if choice_action == forced_choice_action:
                                
                                choice = ( choice_action, choice_tag )
                                
                                break
                                
                            
                        
                        if choice is not None:
                            
                            break
                            
                        
                    
                    if choice is None:
                        
                        intro = 'What would you like to do?'
                        
                        show_always_checkbox = len( sets_of_choices ) > 1
                        
                        with ClientGUIDialogs.DialogButtonChoice( self, intro, choices, show_always_checkbox = show_always_checkbox ) as dlg:
                            
                            result = dlg.ShowModal()
                            
                            if result == wx.ID_OK:
                                
                                ( always_do, choice ) = dlg.GetData()
                                
                            else:
                                
                                break
                                
                            
                        
                    
                
                if choice is None:
                    
                    continue
                    
                
                ( choice_action, choice_tag ) = choice
                
                if always_do:
                    
                    forced_choice_actions.append( choice_action )
                    
                
                if choice_action == HC.CONTENT_UPDATE_ADD: media_to_affect = ( m for m in self._media if choice_tag not in m.GetTagsManager().GetCurrent( self._tag_service_key ) )
                elif choice_action == HC.CONTENT_UPDATE_DELETE: media_to_affect = ( m for m in self._media if choice_tag in m.GetTagsManager().GetCurrent( self._tag_service_key ) )
                elif choice_action == HC.CONTENT_UPDATE_PEND: media_to_affect = ( m for m in self._media if choice_tag not in m.GetTagsManager().GetCurrent( self._tag_service_key ) and choice_tag not in m.GetTagsManager().GetPending( self._tag_service_key ) )
                elif choice_action == HC.CONTENT_UPDATE_PETITION: media_to_affect = ( m for m in self._media if choice_tag in m.GetTagsManager().GetCurrent( self._tag_service_key ) and choice_tag not in m.GetTagsManager().GetPetitioned( self._tag_service_key ) )
                elif choice_action == HC.CONTENT_UPDATE_RESCIND_PEND: media_to_affect = ( m for m in self._media if choice_tag in m.GetTagsManager().GetPending( self._tag_service_key ) )
                elif choice_action == HC.CONTENT_UPDATE_RESCIND_PETITION: media_to_affect = ( m for m in self._media if choice_tag in m.GetTagsManager().GetPetitioned( self._tag_service_key ) )
                
                hashes = set( itertools.chain.from_iterable( ( m.GetHashes() for m in media_to_affect ) ) )
                
                content_updates = []
                
                if choice_action == HC.CONTENT_UPDATE_PETITION:
                    
                    if forced_reason is None:
                        
                        message = 'Enter a reason for ' + choice_tag + ' to be removed. A janitor will review your petition.'
                        
                        with ClientGUIDialogs.DialogTextEntry( self, message ) as dlg:
                            
                            if dlg.ShowModal() == wx.ID_OK:
                                
                                reason = dlg.GetValue()
                                
                            else:
                                
                                continue
                                
                            
                        
                        
                    else:
                        
                        reason = forced_reason
                        
                    
                    content_updates.append( HydrusData.ContentUpdate( HC.CONTENT_TYPE_MAPPINGS, choice_action, ( choice_tag, hashes, reason ) ) )
                    
                else:
                    
                    content_updates.append( HydrusData.ContentUpdate( HC.CONTENT_TYPE_MAPPINGS, choice_action, ( choice_tag, hashes ) ) )
                    
                
                if choice_action in ( HC.CONTENT_UPDATE_ADD, HC.CONTENT_UPDATE_PEND ):
                    
                    tag_parents_manager = HydrusGlobals.client_controller.GetManager( 'tag_parents' )
                    
                    parents = tag_parents_manager.GetParents( self._tag_service_key, choice_tag )
                    
                    content_updates.extend( ( HydrusData.ContentUpdate( HC.CONTENT_TYPE_MAPPINGS, choice_action, ( parent, hashes ) ) for parent in parents ) )
                    
                
                for m in self._media:
                    
                    for content_update in content_updates:
                        
                        m.GetMediaResult().ProcessContentUpdate( self._tag_service_key, content_update )
                        
                    
                
                if self._immediate_commit:
                    
                    if len( content_updates ) > 0:
                        
                        service_keys_to_content_updates = { self._tag_service_key : content_updates }
                        
                        HydrusGlobals.client_controller.WriteSynchronous( 'content_updates', service_keys_to_content_updates )
                        
                    
                else:
                    
                    self._content_updates.extend( content_updates )
                    
                
            
            self._tags_box.SetTagsByMedia( self._media, force_reload = True )
            
        
        def AddTags( self, tags ):
            
            if len( tags ) > 0:
                
                self._AddTags( tags )
                
            
        
        def EnterTags( self, tags, only_add = False ):
            
            if self._collapse_siblings_checkbox.GetValue():
                
                siblings_manager = HydrusGlobals.client_controller.GetManager( 'tag_siblings' )
                
                tags = siblings_manager.CollapseTags( tags )
                
            
            if len( tags ) > 0:
                
                self._AddTags( tags, only_add = only_add )
                
            
        
        def EventAdvancedContentUpdate( self, event ):
            
            hashes = set()
            
            for m in self._media:
                
                hashes.update( m.GetHashes() )
                
            
            self.Ok()
        
            parent = self.GetTopLevelParent().GetParent()
            
            def do_it():
                
                with ClientGUIDialogs.DialogAdvancedContentUpdate( parent, self._tag_service_key, hashes ) as dlg:
                    
                    dlg.ShowModal()
                    
                
            
            wx.CallAfter( do_it )
            
        
        def EventCheckCollapseSiblings( self, event ):
            
            self._new_options.SetBoolean( 'replace_siblings_on_manage_tags', self._collapse_siblings_checkbox.GetValue() )
            
        
        def EventCopyTags( self, event ):
        
            ( current_tags_to_count, deleted_tags_to_count, pending_tags_to_count, petitioned_tags_to_count ) = ClientData.GetMediasTagCount( self._media, tag_service_key = self._tag_service_key, collapse_siblings = False )
            
            tags = set( current_tags_to_count.keys() ).union( pending_tags_to_count.keys() )
            
            text = os.linesep.join( tags )
            
            HydrusGlobals.client_controller.pub( 'clipboard', 'text', text )
            
        
        def EventModify( self, event ):
            
            contents = []
            
            tags = self._tags_box.GetSelectedTags()
            
            hashes = set( itertools.chain.from_iterable( ( m.GetHashes() for m in self._media ) ) )
            
            for tag in tags:
                
                contents.extend( [ HydrusData.Content( HC.CONTENT_TYPE_MAPPING, ( tag, hash ) ) for hash in hashes ] )
                
            
            if len( contents ) > 0:
                
                subject_identifiers = [ HydrusData.AccountIdentifier( content = content ) for content in contents ]
                
                with ClientGUIDialogs.DialogModifyAccounts( self, self._tag_service_key, subject_identifiers ) as dlg: dlg.ShowModal()
                
            
        
        def EventPasteTags( self, event ):
            
            if wx.TheClipboard.Open():
                
                data = wx.TextDataObject()
                
                wx.TheClipboard.GetData( data )
                
                wx.TheClipboard.Close()
                
                text = data.GetText()
                
                try:
                    
                    tags = HydrusData.DeserialisePrettyTags( text )
                    
                    tags = HydrusTags.CleanTags( tags )
                    
                    self.EnterTags( tags, only_add = True )
                    
                except: wx.MessageBox( 'I could not understand what was in the clipboard' )
                
            else: wx.MessageBox( 'I could not get permission to access the clipboard.' )
            
        
        def EventRemoveTags( self, event ):
            
            tag_managers = [ m.GetTagsManager() for m in self._media ]
            
            removable_tags = set()
            
            for tag_manager in tag_managers:
                
                removable_tags.update( tag_manager.GetCurrent( self._tag_service_key ) )
                removable_tags.update( tag_manager.GetPending( self._tag_service_key ) )
                
            
            self._AddTags( removable_tags, only_remove = True )
            
        
        def EventShowDeleted( self, event ):
            
            self._tags_box.SetShow( 'deleted', self._show_deleted_checkbox.GetValue() )
            
        
        def GetContentUpdates( self ): return ( self._tag_service_key, self._content_updates )
        
        def HasChanges( self ):
            
            return len( self._content_updates ) > 0
            
        
        def Ok( self ):
            
            wx.PostEvent( self, wx.CommandEvent( commandType = wx.wxEVT_COMMAND_MENU_SELECTED, winid = ClientCaches.MENU_EVENT_ID_TO_ACTION_CACHE.GetTemporaryId( 'ok' ) ) )
            
        
        def SetMedia( self, media ):
            
            if media is None:
                
                media = []
                
            
            self._media = media
            
            self._tags_box.SetTagsByMedia( self._media )
            
        
        def SetTagBoxFocus( self ):
            
            self._add_tag_box.SetFocus()
            
        
    
class ReviewPanel( wx.lib.scrolledpanel.ScrolledPanel ):
    
    pass
    
class ReviewServices( ReviewPanel ):
    
    def __init__( self, parent, controller ):
        
        self._controller = controller
        
        ReviewPanel.__init__( self, parent )
        
        self._notebook = wx.Notebook( self )
        
        self._local_listbook = ClientGUICommon.ListBook( self._notebook )
        self._remote_listbook = ClientGUICommon.ListBook( self._notebook )
        
        self._edit = wx.Button( self, label = 'manage services' )
        self._edit.Bind( wx.EVT_BUTTON, self.EventEdit )
        
        self._InitialiseServices()
        
        self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
        
        self._notebook.AddPage( self._local_listbook, 'local' )
        self._notebook.AddPage( self._remote_listbook, 'remote' )
        
        self.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.EventPageChanged )
        self.Bind( CC.EVT_SIZE_CHANGED, self.EventPageChanged )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        vbox.AddF( self._notebook, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.AddF( self._edit, CC.FLAGS_SMALL_INDENT )
        
        self.SetSizer( vbox )
        
        self._controller.sub( self, 'RefreshServices', 'notify_new_services_gui' )
        
    
    def _InitialiseServices( self ):
        
        self._local_listbook.DeleteAllPages()
        self._remote_listbook.DeleteAllPages()
        
        listbook_dict = {}
        
        services = self._controller.GetServicesManager().GetServices()
        
        for service in services:
            
            service_type = service.GetServiceType()
            
            if service_type in HC.LOCAL_SERVICES: parent_listbook = self._local_listbook
            else: parent_listbook = self._remote_listbook
            
            if service_type not in listbook_dict:
                
                if service_type == HC.TAG_REPOSITORY: name = 'tag repositories'
                elif service_type == HC.FILE_REPOSITORY: name = 'file repositories'
                elif service_type == HC.MESSAGE_DEPOT: name = 'message depots'
                elif service_type == HC.SERVER_ADMIN: name = 'administrative servers'
                elif service_type == HC.LOCAL_FILE: name = 'files'
                elif service_type == HC.LOCAL_TAG: name = 'tags'
                elif service_type == HC.LOCAL_RATING_LIKE: name = 'like/dislike ratings'
                elif service_type == HC.LOCAL_RATING_NUMERICAL: name = 'numerical ratings'
                elif service_type == HC.LOCAL_BOORU: name = 'booru'
                elif service_type == HC.IPFS: name = 'ipfs'
                else: continue
                
                listbook = ClientGUICommon.ListBook( parent_listbook )
                
                listbook_dict[ service_type ] = listbook
                
                parent_listbook.AddPage( name, name, listbook )
                
            
            listbook = listbook_dict[ service_type ]
            
            name = service.GetName()
            
            listbook.AddPageArgs( name, name, self._Panel, ( listbook, self._controller, service.GetServiceKey() ), {} )
            
        
    
    def EventPageChanged( self, event ):
        
        self.SetVirtualSize( self.DoGetBestSize() )
        
        wx.PostEvent( self.GetParent(), CC.SizeChangedEvent( -1 ) )
        
    
    def DoGetBestSize( self ):
        
        # wx.Notebook isn't expanding on page change and hence increasing min/virtual size and so on to the scrollable panel above, nullifying the neat expand-on-change-page event
        # so, until I write my own or figure out a clever solution, let's just force it
        
        if hasattr( self, '_notebook' ):
            
            current_page = self._notebook.GetCurrentPage()
            
            ( notebook_width, notebook_height ) = self._notebook.GetSize()
            ( page_width, page_height ) = current_page.GetSize()
            
            extra_width = notebook_width - page_width
            extra_height = notebook_height - page_height
            
            ( page_best_width, page_best_height ) = current_page.GetBestSize()
            
            best_size = ( page_best_width + extra_width, page_best_height + extra_height )
            
            return best_size
            
        else:
            
            return ( -1, -1 )
            
        
    
    def EventEdit( self, event ):
        
        original_pause_status = HC.options[ 'pause_repo_sync' ]
        
        HC.options[ 'pause_repo_sync' ] = True
        
        try:
            
            import ClientGUIDialogsManage
            
            with ClientGUIDialogsManage.DialogManageServices( self ) as dlg:
                
                dlg.ShowModal()
                
            
        except: wx.MessageBox( traceback.format_exc() )
        
        HC.options[ 'pause_repo_sync' ] = original_pause_status
        
    
    def RefreshServices( self ):
        
        self._InitialiseServices()
        
    
    class _Panel( wx.Panel ):
        
        def __init__( self, parent, controller, service_key ):
            
            wx.Panel.__init__( self, parent )
            
            self._controller = controller
            self._service_key = service_key
            
            self._service = self._controller.GetServicesManager().GetService( service_key )
            
            service_type = self._service.GetServiceType()
            
            if service_type in HC.REPOSITORIES + HC.LOCAL_SERVICES + [ HC.IPFS ]:
                
                self._info_panel = ClientGUICommon.StaticBox( self, 'service information' )
                
                if service_type in ( HC.LOCAL_FILE, HC.FILE_REPOSITORY ): 
                    
                    self._files_text = wx.StaticText( self._info_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                    
                    self._deleted_files_text = wx.StaticText( self._info_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                    
                elif service_type in HC.TAG_SERVICES:
                    
                    self._tags_text = wx.StaticText( self._info_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                    
                    if service_type == HC.TAG_REPOSITORY:
                        
                        self._deleted_tags_text = wx.StaticText( self._info_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                        
                    
                elif service_type in ( HC.LOCAL_RATING_LIKE, HC.LOCAL_RATING_NUMERICAL ):
                    
                    self._ratings_text = wx.StaticText( self._info_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                    
                elif service_type == HC.LOCAL_BOORU:
                    
                    self._num_shares = wx.StaticText( self._info_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                    
                    self._bytes = ClientGUICommon.Gauge( self._info_panel )
                    
                    self._bytes_text = wx.StaticText( self._info_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                    
                elif service_type == HC.IPFS:
                    
                    self._files_text = wx.StaticText( self._info_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                    
                
            
            if service_type in HC.RESTRICTED_SERVICES:
                
                self._permissions_panel = ClientGUICommon.StaticBox( self, 'service permissions' )
                
                self._account_type = wx.StaticText( self._permissions_panel, style = wx.ALIGN_CENTER )
                
                self._age = ClientGUICommon.Gauge( self._permissions_panel )
                
                self._age_text = wx.StaticText( self._permissions_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                
                self._bytes = ClientGUICommon.Gauge( self._permissions_panel )
                
                self._bytes_text = wx.StaticText( self._permissions_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                
                self._requests = ClientGUICommon.Gauge( self._permissions_panel )
                
                self._requests_text = wx.StaticText( self._permissions_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                
            
            if service_type in HC.REPOSITORIES:
                
                self._synchro_panel = ClientGUICommon.StaticBox( self, 'repository synchronisation' )
                
                self._updates = ClientGUICommon.Gauge( self._synchro_panel )
                
                self._updates_text = wx.StaticText( self._synchro_panel, style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
                
                self._immediate_sync = wx.Button( self._synchro_panel, label = 'sync now' )
                self._immediate_sync.Bind( wx.EVT_BUTTON, self.EventImmediateSync)
                
            
            if service_type == HC.LOCAL_BOORU:
                
                self._booru_shares_panel = ClientGUICommon.StaticBox( self, 'shares' )
                
                self._booru_shares = ClientGUICommon.SaneListCtrl( self._booru_shares_panel, -1, [ ( 'title', 110 ), ( 'text', -1 ), ( 'expires', 170 ), ( 'num files', 70 ) ], delete_key_callback = self.DeleteBoorus )
                
                self._booru_open_search = wx.Button( self._booru_shares_panel, label = 'open share in new page' )
                self._booru_open_search.Bind( wx.EVT_BUTTON, self.EventBooruOpenSearch )
                
                self._copy_internal_share_link = wx.Button( self._booru_shares_panel, label = 'copy internal share link' )
                self._copy_internal_share_link.Bind( wx.EVT_BUTTON, self.EventCopyInternalShareURL )
                
                self._copy_external_share_link = wx.Button( self._booru_shares_panel, label = 'copy external share link' )
                self._copy_external_share_link.Bind( wx.EVT_BUTTON, self.EventCopyExternalShareURL )
                
                self._booru_edit = wx.Button( self._booru_shares_panel, label = 'edit' )
                self._booru_edit.Bind( wx.EVT_BUTTON, self.EventBooruEdit )
                
                self._booru_delete = wx.Button( self._booru_shares_panel, label = 'delete' )
                self._booru_delete.Bind( wx.EVT_BUTTON, self.EventBooruDelete )
                
            
            if service_type == HC.IPFS:
                
                self._ipfs_shares_panel = ClientGUICommon.StaticBox( self, 'pinned directories' )
                
                self._ipfs_shares = ClientGUICommon.SaneListCtrl( self._ipfs_shares_panel, -1, [ ( 'multihash', 110 ), ( 'num files', 70 ), ( 'total size', 70 ), ( 'note', 200 ) ], delete_key_callback = self.UnpinIPFSDirectories )
                
                self._ipfs_open_search = wx.Button( self._ipfs_shares_panel, label = 'open share in new page' )
                self._ipfs_open_search.Bind( wx.EVT_BUTTON, self.EventIPFSOpenSearch )
                
                self._ipfs_set_note = wx.Button( self._ipfs_shares_panel, label = 'set note' )
                self._ipfs_set_note.Bind( wx.EVT_BUTTON, self.EventIPFSSetNote )
                
                self._copy_multihash = wx.Button( self._ipfs_shares_panel, label = 'copy multihash' )
                self._copy_multihash.Bind( wx.EVT_BUTTON, self.EventIPFSCopyMultihash )
                
                self._ipfs_delete = wx.Button( self._ipfs_shares_panel, label = 'unpin' )
                self._ipfs_delete.Bind( wx.EVT_BUTTON, self.EventIPFSUnpin )
                
            
            if service_type in HC.TAG_SERVICES:
                
                self._service_wide_update = wx.Button( self, label = 'advanced service-wide operation' )
                self._service_wide_update.Bind( wx.EVT_BUTTON, self.EventServiceWideUpdate )
                
            
            if self._service_key == CC.LOCAL_FILE_SERVICE_KEY:
                
                self._delete_local_deleted = wx.Button( self, label = 'clear deleted file record' )
                self._delete_local_deleted.SetToolTipString( 'Make the client forget which files it has deleted from local files, resetting all the \'exclude already deleted files\' checks.' )
                self._delete_local_deleted.Bind( wx.EVT_BUTTON, self.EventDeleteLocalDeleted )
                
            
            if self._service_key == CC.TRASH_SERVICE_KEY:
                
                self._clear_trash = wx.Button( self, label = 'clear trash' )
                self._clear_trash.Bind( wx.EVT_BUTTON, self.EventClearTrash )
                
            
            if service_type == HC.SERVER_ADMIN:
                
                self._init = wx.Button( self, label = 'initialise server' )
                self._init.Bind( wx.EVT_BUTTON, self.EventServerInitialise )
                
            
            if service_type in HC.RESTRICTED_SERVICES:
                
                self._refresh = wx.Button( self, label = 'refresh account' )
                self._refresh.Bind( wx.EVT_BUTTON, self.EventServiceRefreshAccount )
                
                self._copy_account_key = wx.Button( self, label = 'copy account key' )
                self._copy_account_key.Bind( wx.EVT_BUTTON, self.EventCopyAccountKey )
                
            
            #
            
            self._DisplayService()
            
            #
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            if service_type in HC.REPOSITORIES + HC.LOCAL_SERVICES + [ HC.IPFS ]:
                
                if service_type in ( HC.LOCAL_FILE, HC.FILE_REPOSITORY ):
                    
                    self._info_panel.AddF( self._files_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                    
                    self._info_panel.AddF( self._deleted_files_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                    
                elif service_type in HC.TAG_SERVICES:
                    
                    self._info_panel.AddF( self._tags_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                    
                    if service_type == HC.TAG_REPOSITORY:
                        
                        self._info_panel.AddF( self._deleted_tags_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                        
                    
                elif service_type in ( HC.LOCAL_RATING_LIKE, HC.LOCAL_RATING_NUMERICAL ):
                    
                    self._info_panel.AddF( self._ratings_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                    
                elif service_type == HC.LOCAL_BOORU:
                    
                    self._info_panel.AddF( self._num_shares, CC.FLAGS_EXPAND_PERPENDICULAR )
                    self._info_panel.AddF( self._bytes, CC.FLAGS_EXPAND_PERPENDICULAR )
                    self._info_panel.AddF( self._bytes_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                    
                elif service_type == HC.IPFS:
                    
                    self._info_panel.AddF( self._files_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                    
                
                vbox.AddF( self._info_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
                
            
            if service_type in HC.RESTRICTED_SERVICES:
                
                self._permissions_panel.AddF( self._account_type, CC.FLAGS_EXPAND_PERPENDICULAR )
                self._permissions_panel.AddF( self._age, CC.FLAGS_EXPAND_PERPENDICULAR )
                self._permissions_panel.AddF( self._age_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                self._permissions_panel.AddF( self._bytes, CC.FLAGS_EXPAND_PERPENDICULAR )
                self._permissions_panel.AddF( self._bytes_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                self._permissions_panel.AddF( self._requests, CC.FLAGS_EXPAND_PERPENDICULAR )
                self._permissions_panel.AddF( self._requests_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                
                vbox.AddF( self._permissions_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
                
            
            if service_type in HC.REPOSITORIES:
                
                self._synchro_panel.AddF( self._updates, CC.FLAGS_EXPAND_PERPENDICULAR )
                self._synchro_panel.AddF( self._updates_text, CC.FLAGS_EXPAND_PERPENDICULAR )
                self._synchro_panel.AddF( self._immediate_sync, CC.FLAGS_LONE_BUTTON )
                
                vbox.AddF( self._synchro_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
                
            
            if service_type == HC.LOCAL_BOORU:
                
                self._booru_shares_panel.AddF( self._booru_shares, CC.FLAGS_EXPAND_BOTH_WAYS )
                
                b_box = wx.BoxSizer( wx.HORIZONTAL )
                b_box.AddF( self._booru_open_search, CC.FLAGS_MIXED )
                b_box.AddF( self._copy_internal_share_link, CC.FLAGS_MIXED )
                b_box.AddF( self._copy_external_share_link, CC.FLAGS_MIXED )
                b_box.AddF( self._booru_edit, CC.FLAGS_MIXED )
                b_box.AddF( self._booru_delete, CC.FLAGS_MIXED )
                
                self._booru_shares_panel.AddF( b_box, CC.FLAGS_BUTTON_SIZER )
                
                vbox.AddF( self._booru_shares_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
                
            
            if service_type == HC.IPFS:
                
                self._ipfs_shares_panel.AddF( self._ipfs_shares, CC.FLAGS_EXPAND_BOTH_WAYS )
                
                b_box = wx.BoxSizer( wx.HORIZONTAL )
                b_box.AddF( self._ipfs_open_search, CC.FLAGS_MIXED )
                b_box.AddF( self._ipfs_set_note, CC.FLAGS_MIXED )
                b_box.AddF( self._copy_multihash, CC.FLAGS_MIXED )
                b_box.AddF( self._ipfs_delete, CC.FLAGS_MIXED )
                
                self._ipfs_shares_panel.AddF( b_box, CC.FLAGS_BUTTON_SIZER )
                
                vbox.AddF( self._ipfs_shares_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
                
            
            if service_type in HC.RESTRICTED_SERVICES + [ HC.LOCAL_TAG ] or self._service_key in ( CC.LOCAL_FILE_SERVICE_KEY, CC.TRASH_SERVICE_KEY ):
                
                repo_buttons_hbox = wx.BoxSizer( wx.HORIZONTAL )
                
                if self._service_key == CC.LOCAL_FILE_SERVICE_KEY:
                    
                    repo_buttons_hbox.AddF( self._delete_local_deleted, CC.FLAGS_MIXED )
                    
                
                if self._service_key == CC.TRASH_SERVICE_KEY:
                    
                    repo_buttons_hbox.AddF( self._clear_trash, CC.FLAGS_MIXED )
                    
                
                if service_type in HC.TAG_SERVICES:
                    
                    repo_buttons_hbox.AddF( self._service_wide_update, CC.FLAGS_MIXED )
                    
                
                if service_type == HC.SERVER_ADMIN:
                    
                    repo_buttons_hbox.AddF( self._init, CC.FLAGS_MIXED )
                    
                
                if service_type in HC.RESTRICTED_SERVICES:
                    
                    repo_buttons_hbox.AddF( self._refresh, CC.FLAGS_MIXED )
                    repo_buttons_hbox.AddF( self._copy_account_key, CC.FLAGS_MIXED )
                    
                
                vbox.AddF( repo_buttons_hbox, CC.FLAGS_BUTTON_SIZER )
                
            
            self.SetSizer( vbox )
            
            self._timer_updates = wx.Timer( self, id = CC.ID_TIMER_UPDATES )
            
            if service_type in HC.REPOSITORIES:
                
                self.Bind( wx.EVT_TIMER, self.TIMEREventUpdates, id = CC.ID_TIMER_UPDATES )
                
                self._timer_updates.Start( 1000, wx.TIMER_CONTINUOUS )
                
            
            self._controller.sub( self, 'ProcessServiceUpdates', 'service_updates_gui' )
            if service_type == HC.LOCAL_BOORU: self._controller.sub( self, 'RefreshLocalBooruShares', 'refresh_local_booru_shares' )
            
        
        def _DisplayAccountInfo( self ):
            
            service_type = self._service.GetServiceType()
            
            now = HydrusData.GetNow()
            
            if service_type == HC.LOCAL_BOORU:
                
                info = self._service.GetInfo()
                
                max_monthly_data = info[ 'max_monthly_data' ]
                used_monthly_data = info[ 'used_monthly_data' ]
                used_monthly_requests = info[ 'used_monthly_requests' ]
                
                if used_monthly_requests == 0: monthly_requests_text = ''
                else: monthly_requests_text = ' in ' + HydrusData.ConvertIntToPrettyString( used_monthly_requests ) + ' requests'
                
                if max_monthly_data is None:
                    
                    self._bytes.Hide()
                    
                    self._bytes_text.SetLabelText( 'used ' + HydrusData.ConvertIntToBytes( used_monthly_data ) + monthly_requests_text + ' this month' )
                    
                else:
                    
                    self._bytes.Show()
                    
                    self._bytes.SetRange( max_monthly_data )
                    self._bytes.SetValue( used_monthly_data )
                    
                    self._bytes_text.SetLabelText( 'used ' + HydrusData.ConvertValueRangeToPrettyString( used_monthly_data, max_monthly_data ) + monthly_requests_text + ' this month' )
                    
                
            
            if service_type in HC.RESTRICTED_SERVICES:
                
                account = self._service.GetInfo( 'account' )
                
                account_type = account.GetAccountType()
                
                account_type_string = account_type.ConvertToString()
                
                if self._account_type.GetLabelText() != account_type_string:
                    
                    self._account_type.SetLabelText( account_type_string )
                    
                    self._account_type.Wrap( 400 )
                    
                
                created = account.GetCreated()
                expires = account.GetExpires()
                
                if expires is None: self._age.Hide()
                else:
                    
                    self._age.Show()
                    
                    self._age.SetRange( expires - created )
                    self._age.SetValue( min( now - created, expires - created ) )
                    
                
                self._age_text.SetLabelText( account.GetExpiresString() )
                
                max_num_bytes = account_type.GetMaxBytes()
                max_num_requests = account_type.GetMaxRequests()
                
                used_bytes = account.GetUsedBytes()
                used_requests = account.GetUsedRequests()
                
                if max_num_bytes is None: self._bytes.Hide()
                else:
                    
                    self._bytes.Show()
                    
                    self._bytes.SetRange( max_num_bytes )
                    self._bytes.SetValue( used_bytes )
                    
                
                self._bytes_text.SetLabelText( account.GetUsedBytesString() )
                
                if max_num_requests is None: self._requests.Hide()
                else:
                    
                    self._requests.Show()
                    
                    self._requests.SetRange( max_num_requests )
                    self._requests.SetValue( min( used_requests, max_num_requests ) )
                    
                
                self._requests_text.SetLabelText( account.GetUsedRequestsString() )
                
                if service_type in HC.REPOSITORIES:
                    
                    ( first_timestamp, next_download_timestamp, next_processing_timestamp ) = self._service.GetTimestamps()
                    
                    if first_timestamp is None:
                        
                        num_updates = 0
                        num_updates_downloaded = 0
                        
                        self._updates.SetValue( 0 )
                        
                    else:
                        
                        num_updates = ( now - first_timestamp ) / HC.UPDATE_DURATION
                        num_updates_downloaded = ( next_download_timestamp - first_timestamp ) / HC.UPDATE_DURATION
                        
                        self._updates.SetRange( num_updates )
                        self._updates.SetValue( num_updates_downloaded )
                        
                    
                    self._updates_text.SetLabelText( self._service.GetUpdateStatus() )
                    
                    if account.HasPermission( HC.RESOLVE_PETITIONS ):
                        
                        self._immediate_sync.Show()
                        
                    else:
                        
                        self._immediate_sync.Hide()
                        
                    
                
                self._refresh.Enable()
                
                if account.HasAccountKey(): self._copy_account_key.Enable()
                else: self._copy_account_key.Disable()
                
            
        
        def _DisplayService( self ):
            
            service_type = self._service.GetServiceType()
            
            self._DisplayAccountInfo()
            
            if service_type in HC.REPOSITORIES + HC.LOCAL_SERVICES + [ HC.IPFS ]:
                
                service_info = self._controller.Read( 'service_info', self._service_key )
                
                if service_type in ( HC.LOCAL_FILE, HC.FILE_REPOSITORY ): 
                    
                    num_files = service_info[ HC.SERVICE_INFO_NUM_FILES ]
                    total_size = service_info[ HC.SERVICE_INFO_TOTAL_SIZE ]
                    
                    self._files_text.SetLabelText( HydrusData.ConvertIntToPrettyString( num_files ) + ' files, totalling ' + HydrusData.ConvertIntToBytes( total_size ) )
                    
                    num_deleted_files = service_info[ HC.SERVICE_INFO_NUM_DELETED_FILES ]
                    
                    self._deleted_files_text.SetLabelText( HydrusData.ConvertIntToPrettyString( num_deleted_files ) + ' deleted files' )
                    
                elif service_type in HC.TAG_SERVICES:
                    
                    num_files = service_info[ HC.SERVICE_INFO_NUM_FILES ]
                    num_tags = service_info[ HC.SERVICE_INFO_NUM_TAGS ]
                    num_mappings = service_info[ HC.SERVICE_INFO_NUM_MAPPINGS ]
                    
                    self._tags_text.SetLabelText( HydrusData.ConvertIntToPrettyString( num_files ) + ' hashes, ' + HydrusData.ConvertIntToPrettyString( num_tags ) + ' tags, totalling ' + HydrusData.ConvertIntToPrettyString( num_mappings ) + ' mappings' )
                    
                    if service_type == HC.TAG_REPOSITORY:
                        
                        num_deleted_mappings = service_info[ HC.SERVICE_INFO_NUM_DELETED_MAPPINGS ]
                        
                        self._deleted_tags_text.SetLabelText( HydrusData.ConvertIntToPrettyString( num_deleted_mappings ) + ' deleted mappings' )
                        
                    
                elif service_type in ( HC.LOCAL_RATING_LIKE, HC.LOCAL_RATING_NUMERICAL ):
                    
                    num_ratings = service_info[ HC.SERVICE_INFO_NUM_FILES ]
                    
                    self._ratings_text.SetLabelText( str( num_ratings ) + ' files rated' )
                    
                elif service_type == HC.LOCAL_BOORU:
                    
                    num_shares = service_info[ HC.SERVICE_INFO_NUM_SHARES ]
                    
                    self._num_shares.SetLabelText( HydrusData.ConvertIntToPrettyString( num_shares ) + ' shares currently active' )
                    
                elif service_type == HC.IPFS:
                    
                    num_files = service_info[ HC.SERVICE_INFO_NUM_FILES ]
                    total_size = service_info[ HC.SERVICE_INFO_TOTAL_SIZE ]
                    
                    self._files_text.SetLabelText( HydrusData.ConvertIntToPrettyString( num_files ) + ' files, totalling ' + HydrusData.ConvertIntToBytes( total_size ) )
                    
                
            
            if service_type == HC.LOCAL_BOORU:
                
                booru_shares = self._controller.Read( 'local_booru_shares' )
                
                self._booru_shares.DeleteAllItems()
                
                for ( share_key, info ) in booru_shares.items():
                    
                    name = info[ 'name' ]
                    text = info[ 'text' ]
                    timeout = info[ 'timeout' ]
                    hashes = info[ 'hashes' ]
                    
                    self._booru_shares.Append( ( name, text, HydrusData.ConvertTimestampToPrettyExpires( timeout ), len( hashes ) ), ( name, text, timeout, ( len( hashes ), hashes, share_key ) ) )
                    
                
            
            if service_type == HC.IPFS:
                
                ipfs_shares = self._controller.Read( 'service_directories', self._service_key )
                
                self._ipfs_shares.DeleteAllItems()
                
                for ( multihash, num_files, total_size, note ) in ipfs_shares:
                    
                    self._ipfs_shares.Append( ( multihash, HydrusData.ConvertIntToPrettyString( num_files ), HydrusData.ConvertIntToBytes( total_size ), note ), ( multihash, num_files, total_size, note ) )
                    
                
            
            if service_type == HC.SERVER_ADMIN:
                
                if self._service.IsInitialised():
                    
                    self._init.Hide()
                    self._refresh.Show()
                    
                else:
                    
                    self._init.Show()
                    self._refresh.Hide()
                    
                
            
        
        def DeleteBoorus( self ):
            
            for ( name, text, timeout, ( num_hashes, hashes, share_key ) ) in self._booru_shares.GetSelectedClientData():
                
                self._controller.Write( 'delete_local_booru_share', share_key )
                
            
            self._booru_shares.RemoveAllSelected()
            
        
        def EventBooruDelete( self, event ):
            
            self.DeleteBoorus()
            
        
        def EventBooruEdit( self, event ):
            
            writes = []
            
            for ( name, text, timeout, ( num_hashes, hashes, share_key ) ) in self._booru_shares.GetSelectedClientData():
                
                with ClientGUIDialogs.DialogInputLocalBooruShare( self, share_key, name, text, timeout, hashes, new_share = False) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        ( share_key, name, text, timeout, hashes ) = dlg.GetInfo()
                        
                        info = {}
                        
                        info[ 'name' ] = name
                        info[ 'text' ] = text
                        info[ 'timeout' ] = timeout
                        info[ 'hashes' ] = hashes
                        
                        writes.append( ( share_key, info ) )
                        
                    
                
            
            for ( share_key, info ) in writes:
                
                self._controller.Write( 'local_booru_share', share_key, info )
                
            
        
        def EventBooruOpenSearch( self, event ):
            
            for ( name, text, timeout, ( num_hashes, hashes, share_key ) ) in self._booru_shares.GetSelectedClientData():
                
                media_results = self._controller.Read( 'media_results', hashes )
                
                self._controller.pub( 'new_page_query', CC.LOCAL_FILE_SERVICE_KEY, initial_media_results = media_results )
                
            
        
        def EventClearTrash( self, event ):
            
            def do_it():
                
                hashes = self._controller.Read( 'trash_hashes' )
                
                content_update = HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_DELETE, hashes )
                
                service_keys_to_content_updates = { CC.TRASH_SERVICE_KEY : [ content_update ] }
                
                self._controller.WriteSynchronous( 'content_updates', service_keys_to_content_updates )
                
                wx.CallAfter( self._DisplayService )
                
            
            self._controller.CallToThread( do_it )
            
        
        def EventCopyAccountKey( self, event ):
            
            account_key = self._service.GetInfo( 'account' ).GetAccountKey()
            
            account_key_hex = account_key.encode( 'hex' )
            
            self._controller.pub( 'clipboard', 'text', account_key_hex )
            
        
        def EventCopyExternalShareURL( self, event ):
            
            shares = self._booru_shares.GetSelectedClientData()
            
            if len( shares ) > 0:
                
                ( name, text, timeout, ( num_hashes, hashes, share_key ) ) = shares[0]
                
                info = self._service.GetInfo()
                
                external_ip = HydrusNATPunch.GetExternalIP() # eventually check for optional host replacement here
                
                external_port = info[ 'upnp' ]
                
                if external_port is None: external_port = info[ 'port' ]
                
                url = 'http://' + external_ip + ':' + str( external_port ) + '/gallery?share_key=' + share_key.encode( 'hex' )
                
                self._controller.pub( 'clipboard', 'text', url )
                
            
        
        def EventCopyInternalShareURL( self, event ):
            
            shares = self._booru_shares.GetSelectedClientData()
            
            if len( shares ) > 0:
                
                ( name, text, timeout, ( num_hashes, hashes, share_key ) ) = shares[0]
                
                info = self._service.GetInfo()
                
                internal_ip = '127.0.0.1'
                
                internal_port = info[ 'port' ]
                
                url = 'http://' + internal_ip + ':' + str( internal_port ) + '/gallery?share_key=' + share_key.encode( 'hex' )
                
                self._controller.pub( 'clipboard', 'text', url )
                
            
        
        def EventDeleteLocalDeleted( self, event ):
            
            message = 'This will clear the client\'s memory of which files it has locally deleted, which affects \'exclude already deleted files\' import tests.'
            message += os.linesep * 2
            message += 'It will freeze the gui while it works.'
            message += os.linesep * 2
            message += 'If you do not know what this does, click \'forget it\'.'
            
            with ClientGUIDialogs.DialogYesNo( self, message, yes_label = 'do it', no_label = 'forget it' ) as dlg_add:
                
                result = dlg_add.ShowModal()
                
                if result == wx.ID_YES:
                    
                    content_update = HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_ADVANCED, ( 'delete_deleted', None ) )
                    
                    service_keys_to_content_updates = { self._service_key : [ content_update ] }
                    
                    HydrusGlobals.client_controller.Write( 'content_updates', service_keys_to_content_updates )
                    
                    self._DisplayService()
                    
                
            
        
        def EventImmediateSync( self, event ):
            
            def do_it():
                
                job_key = ClientThreading.JobKey( pausable = True, cancellable = True )
                
                job_key.SetVariable( 'popup_title', self._service.GetName() + ': immediate sync' )
                job_key.SetVariable( 'popup_text_1', 'downloading' )
                
                self._controller.pub( 'message', job_key )
                
                content_update_package = self._service.Request( HC.GET, 'immediate_content_update_package' )
                
                c_u_p_num_rows = content_update_package.GetNumRows()
                c_u_p_total_weight_processed = 0
                
                update_speed_string = ''
                
                content_update_index_string = 'content row ' + HydrusData.ConvertValueRangeToPrettyString( c_u_p_total_weight_processed, c_u_p_num_rows ) + ': '
                
                job_key.SetVariable( 'popup_text_1', content_update_index_string + 'committing' + update_speed_string )
                
                job_key.SetVariable( 'popup_gauge_1', ( c_u_p_total_weight_processed, c_u_p_num_rows ) )
                
                for ( content_updates, weight ) in content_update_package.IterateContentUpdateChunks():
                    
                    ( i_paused, should_quit ) = job_key.WaitIfNeeded()
                    
                    if should_quit:
                        
                        job_key.Delete()
                        
                        return
                        
                    
                    content_update_index_string = 'content row ' + HydrusData.ConvertValueRangeToPrettyString( c_u_p_total_weight_processed, c_u_p_num_rows ) + ': '
                    
                    job_key.SetVariable( 'popup_text_1', content_update_index_string + 'committing' + update_speed_string )
                    
                    job_key.SetVariable( 'popup_gauge_1', ( c_u_p_total_weight_processed, c_u_p_num_rows ) )
                    
                    precise_timestamp = HydrusData.GetNowPrecise()
                    
                    self._controller.WriteSynchronous( 'content_updates', { self._service_key : content_updates } )
                    
                    it_took = HydrusData.GetNowPrecise() - precise_timestamp
                    
                    rows_s = weight / it_took
                    
                    update_speed_string = ' at ' + HydrusData.ConvertIntToPrettyString( rows_s ) + ' rows/s'
                    
                    c_u_p_total_weight_processed += weight
                    
                
                job_key.DeleteVariable( 'popup_gauge_1' )
                
                self._service.SyncThumbnails( job_key )
                
                job_key.SetVariable( 'popup_text_1', 'done! ' + HydrusData.ConvertIntToPrettyString( c_u_p_num_rows ) + ' rows added.' )
                
                job_key.Finish()
                
            
            self._controller.CallToThread( do_it )
            
        
        def EventIPFSCopyMultihash( self, event ):
            
            shares = self._ipfs_shares.GetSelectedClientData()
            
            if len( shares ) > 0:
                
                ( multihash, num_files, total_size, note ) = shares[0]
                
                multihash_prefix = self._service.GetInfo( 'multihash_prefix' )
                
                text = multihash_prefix + multihash
                
                self._controller.pub( 'clipboard', 'text', text )
                
            
        
        def EventIPFSOpenSearch( self, event ):
            
            for ( multihash, num_files, total_size, note ) in self._ipfs_shares.GetSelectedClientData():
                
                hashes = self._controller.Read( 'service_directory', self._service_key, multihash )
                
                media_results = self._controller.Read( 'media_results', hashes )
                
                self._controller.pub( 'new_page_query', CC.LOCAL_FILE_SERVICE_KEY, initial_media_results = media_results )
                
            
        
        def EventIPFSSetNote( self, event ):
            
            for ( multihash, num_files, total_size, note ) in self._ipfs_shares.GetSelectedClientData():
                
                with ClientGUIDialogs.DialogTextEntry( self, 'Set a note for ' + multihash + '.' ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        hashes = self._controller.Read( 'service_directory', self._service_key, multihash )
                        
                        note = dlg.GetValue()
                        
                        content_update_row = ( hashes, multihash, note )
                        
                        content_updates = [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_DIRECTORIES, HC.CONTENT_UPDATE_ADD, content_update_row ) ]
                        
                        HydrusGlobals.client_controller.WriteSynchronous( 'content_updates', { self._service_key : content_updates } )
                        
                    
                
            
            self._DisplayService()
            
        
        def EventIPFSUnpin( self, event ):
            
            self.UnpinIPFSDirectories()
            
        
        def EventServiceWideUpdate( self, event ):
            
            with ClientGUIDialogs.DialogAdvancedContentUpdate( self, self._service_key ) as dlg:
                
                dlg.ShowModal()
                
            
        
        def EventServerInitialise( self, event ):
            
            service_key = self._service.GetServiceKey()
            service_type = self._service.GetServiceType()
            name = self._service.GetName()
            
            response = self._service.Request( HC.GET, 'init' )
            
            access_key = response[ 'access_key' ]
            
            info_update = { 'access_key' : access_key }
            
            edit_log = [ HydrusData.EditLogActionEdit( service_key, ( service_key, service_type, name, info_update ) ) ]
            
            self._controller.Write( 'update_services', edit_log )
            
            ClientGUITopLevelWindows.ShowKeys( 'access', ( access_key, ) )
            
        
        def EventServiceRefreshAccount( self, event ):
            
            self._refresh.Disable()
            
            def do_it():
                
                try:
                    
                    response = self._service.Request( HC.GET, 'account' )
                    
                    account = response[ 'account' ]
                    
                    account.MakeFresh()
                    
                    self._controller.Write( 'service_updates', { self._service_key : [ HydrusData.ServiceUpdate( HC.SERVICE_UPDATE_ACCOUNT, account ) ] } )
                    
                except:
                    
                    wx.CallAfter( self._refresh.Enable )
                    
                    raise
                    
                
            
            self._controller.CallToThread( do_it )
            
        
        def ProcessServiceUpdates( self, service_keys_to_service_updates ):
            
            for ( service_key, service_updates ) in service_keys_to_service_updates.items():
                
                for service_update in service_updates:
                    
                    if service_key == self._service_key:
                        
                        ( action, row ) = service_update.ToTuple()
                        
                        if action in ( HC.SERVICE_UPDATE_ACCOUNT, HC.SERVICE_UPDATE_REQUEST_MADE ):
                            
                            self._DisplayAccountInfo()
                            
                        else:
                            
                            self._DisplayService()
                            
                        
                        self.Layout()
                        
                    
                
            
        
        def RefreshLocalBooruShares( self ):
            
            self._DisplayService()
            
        
        def UnpinIPFSDirectories( self ):
            
            for ( multihash, num_files, total_size, note ) in self._ipfs_shares.GetSelectedClientData():
                
                self._service.UnpinDirectory( multihash )
                
            
            self._ipfs_shares.RemoveAllSelected()
            
        
        def TIMEREventUpdates( self, event ):
            
            try:
                
                self._updates_text.SetLabelText( self._service.GetUpdateStatus() )
                
            except wx.PyDeadObjectError:
                
                self._timer_updates.Stop()
                
            except:
                
                self._timer_updates.Stop()
                
                raise
                
            
        
    