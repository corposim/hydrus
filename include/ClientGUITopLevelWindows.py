import ClientCaches
import ClientConstants as CC
import ClientGUIMenus
import ClientGUIShortcuts
import HydrusConstants as HC
import HydrusData
import HydrusExceptions
import HydrusGlobals as HG
import os
import wx

( OKEvent, EVT_OK ) = wx.lib.newevent.NewCommandEvent()

CHILD_POSITION_PADDING = 24
FUZZY_PADDING = 15

def GetDisplayPosition( window ):
    
    display_index = wx.Display.GetFromWindow( window )
    
    if display_index == wx.NOT_FOUND:
        
        display_index = 0 # default to primary
        
    
    display = wx.Display( display_index )
    
    rect = display.GetClientArea()
    
    return tuple( rect.GetPosition() )
    
def GetDisplaySize( window ):
    
    display_index = wx.Display.GetFromWindow( window )
    
    if display_index == wx.NOT_FOUND:
        
        display_index = 0 # default to primary
        
    
    display = wx.Display( display_index )
    
    rect = display.GetClientArea()
    
    return tuple( rect.GetSize() )
    
def GetSafePosition( position ):
    
    ( p_x, p_y ) = position
    
    # some window managers size the windows just off screen to cut off borders
    # so choose a test position that's a little more lenient
    ( test_x, test_y ) = ( p_x + FUZZY_PADDING, p_y + FUZZY_PADDING )
    
    display_index = wx.Display.GetFromPoint( ( test_x, test_y ) )
    
    if display_index == wx.NOT_FOUND:
        
        return wx.DefaultPosition
        
    else:
        
        return position
        
    
def GetSafeSize( tlw, min_size, gravity ):
    
    ( min_width, min_height ) = min_size
    
    parent = tlw.GetParent()
    
    if parent is None:
        
        width = min_width
        height = min_height
        
    else:
        
        ( parent_window_width, parent_window_height ) = parent.GetTopLevelParent().GetSize()
        
        ( width_gravity, height_gravity ) = gravity
        
        if width_gravity == -1:
            
            width = min_width
            
        else:
            
            max_width = parent_window_width - 2 * CHILD_POSITION_PADDING
            
            width = int( width_gravity * max_width )
            
        
        if height_gravity == -1:
            
            height = min_height
            
        else:
            
            max_height = parent_window_height - 2 * CHILD_POSITION_PADDING
            
            height = int( height_gravity * max_height )
            
        
    
    ( display_width, display_height ) = GetDisplaySize( tlw )
    
    width = min( display_width, width )
    height = min( display_height, height )
    
    return ( width, height )
    
def ExpandTLWIfPossible( tlw, frame_key, desired_size_delta ):
    
    new_options = HG.client_controller.new_options
    
    ( remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = new_options.GetFrameLocation( frame_key )
    
    if not tlw.IsMaximized() and not tlw.IsFullScreen():
        
        ( current_width, current_height ) = tlw.GetSize()
        
        ( desired_delta_width, desired_delta_height ) = desired_size_delta
        
        desired_width = current_width + desired_delta_width + FUZZY_PADDING
        desired_height = current_height + desired_delta_height + FUZZY_PADDING
        
        ( width, height ) = GetSafeSize( tlw, ( desired_width, desired_height ), default_gravity )
        
        if width > current_width or height > current_height:
            
            tlw.SetSize( ( width, height ) )
            
            SlideOffScreenTLWUpAndLeft( tlw )
            
        
    
def MouseIsOnMyDisplay( window ):
    
    window_display_index = wx.Display.GetFromWindow( window )
    
    mouse_display_index = wx.Display.GetFromPoint( wx.GetMousePosition() )
    
    return window_display_index == mouse_display_index
    
def PostSizeChangedEvent( window ):
    
    event = CC.SizeChangedEvent( -1 )
    
    wx.QueueEvent( window.GetEventHandler(), event )
    
def SaveTLWSizeAndPosition( tlw, frame_key ):
    
    new_options = HG.client_controller.new_options
    
    ( remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = new_options.GetFrameLocation( frame_key )
    
    maximised = tlw.IsMaximized()
    fullscreen = tlw.IsFullScreen()
    
    if not ( maximised or fullscreen ):
        
        safe_position = GetSafePosition( tuple( tlw.GetPosition() ) )
        
        if safe_position != wx.DefaultPosition:
            
            last_size = tuple( tlw.GetSize() )
            last_position = safe_position
            
        
    
    new_options.SetFrameLocation( frame_key, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen )
    
def SetInitialTLWSizeAndPosition( tlw, frame_key ):
    
    new_options = HG.client_controller.new_options
    
    ( remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = new_options.GetFrameLocation( frame_key )
    
    parent = tlw.GetParent()
    
    if remember_size and last_size is not None:
        
        ( width, height ) = last_size
        
    else:
        
        ( min_width, min_height ) = tlw.GetEffectiveMinSize()
        
        min_width += FUZZY_PADDING
        min_height += FUZZY_PADDING
        
        ( width, height ) = GetSafeSize( tlw, ( min_width, min_height ), default_gravity )
        
    
    tlw.SetInitialSize( ( width, height ) )
    
    min_width = min( 240, width )
    min_height = min( 240, height )
    
    tlw.SetMinSize( ( min_width, min_height ) )
    
    #
    
    if remember_position and last_position is not None:
        
        safe_position = GetSafePosition( last_position )
        
        tlw.SetPosition( safe_position )
        
    elif default_position == 'topleft':
        
        if parent is not None:
            
            if isinstance( parent, wx.TopLevelWindow ):
                
                parent_tlp = parent
                
            else:
                
                parent_tlp = parent.GetTopLevelParent()
                
            
            ( parent_x, parent_y ) = parent_tlp.GetPosition()
            
            tlw.SetPosition( ( parent_x + CHILD_POSITION_PADDING, parent_y + CHILD_POSITION_PADDING ) )
            
        else:
            
            safe_position = GetSafePosition( ( 0 + CHILD_POSITION_PADDING, 0 + CHILD_POSITION_PADDING ) )
            
            tlw.SetPosition( safe_position )
            
        
        SlideOffScreenTLWUpAndLeft( tlw )
        
    elif default_position == 'center':
        
        wx.CallAfter( tlw.Center )
        
    
    # if these aren't callafter, the size and pos calls don't stick if a restore event happens
    
    if maximised:
        
        wx.CallAfter( tlw.Maximize )
        
    
    if fullscreen:
        
        wx.CallAfter( tlw.ShowFullScreen, True, wx.FULLSCREEN_ALL )
        
    
def SlideOffScreenTLWUpAndLeft( tlw ):
    
    ( tlw_width, tlw_height ) = tlw.GetSize()
    ( tlw_x, tlw_y ) = tlw.GetPosition()
    
    tlw_right = tlw_x + tlw_width
    tlw_bottom = tlw_y + tlw_height
    
    ( display_width, display_height ) = GetDisplaySize( tlw )
    ( display_x, display_y ) = GetDisplayPosition( tlw )
    
    display_right = display_x + display_width
    display_bottom = display_y + display_height
    
    move_x = tlw_right > display_right
    move_y = tlw_bottom > display_bottom
    
    if move_x or move_y:
        
        delta_x = min( display_right - tlw_right, 0 )
        delta_y = min( display_bottom - tlw_bottom, 0 )
        
        tlw.SetPosition( ( tlw_x + delta_x, tlw_y + delta_y ) )
        
    
class NewDialog( wx.Dialog ):
    
    def __init__( self, parent, title, style_override = None ):
        
        if style_override is None:
            
            style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
            
            if not HC.PLATFORM_LINUX and parent is not None:
                
                style |= wx.FRAME_FLOAT_ON_PARENT
                
            
        else:
            
            style = style_override
            
        
        wx.Dialog.__init__( self, parent, title = title, style = style )
        
        self._new_options = HG.client_controller.new_options
        
        self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_FRAMEBK ) )
        
        self.SetIcon( HG.client_controller.frame_icon )
        
        self.Bind( wx.EVT_BUTTON, self.EventDialogButton )
        
        self.Bind( wx.EVT_MENU_CLOSE, self.EventMenuClose )
        self.Bind( wx.EVT_MENU_HIGHLIGHT_ALL, self.EventMenuHighlight )
        self.Bind( wx.EVT_MENU_OPEN, self.EventMenuOpen )
        
        self._menu_stack = []
        self._menu_text_stack = []
        
        HG.client_controller.ResetIdleTimer()
        
    
    def _CanCancel( self ):
        
        return True
        
    
    def EventMenuClose( self, event ):
        
        menu = event.GetMenu()
        
        if menu is not None and menu in self._menu_stack:
            
            index = self._menu_stack.index( menu )
            
            del self._menu_stack[ index ]
            
            previous_text = self._menu_text_stack.pop()
            
            status_bar = HG.client_controller.GetGUI().GetStatusBar()
            
            status_bar.SetStatusText( previous_text )
            
        
    
    def EventMenuHighlight( self, event ):
        
        if len( self._menu_stack ) > 0:
            
            text = ''
            
            menu = self._menu_stack[-1]
            
            while ClientGUIMenus.MenuIsDead( menu ):
                
                if len( self._menu_stack ) == 0:
                    
                    return
                    
                
                del self._menu_stack[-1]
                
                menu = self._menu_stack[-1]
                
            
            menu_item = menu.FindItemById( event.GetMenuId() )
            
            if menu_item is not None:
                
                text = menu_item.GetHelp()
                
            
            status_bar = HG.client_controller.GetGUI().GetStatusBar()
            
            status_bar.SetStatusText( text )
            
        
    
    def EventMenuOpen( self, event ):
        
        menu = event.GetMenu()
        
        if menu is not None:
            
            status_bar = HG.client_controller.GetGUI().GetStatusBar()
            
            previous_text = status_bar.GetStatusText()
            
            self._menu_stack.append( menu )
            
            self._menu_text_stack.append( previous_text )
            
        
    
    def EventDialogButton( self, event ):
        
        event_id = event.GetId()
        
        if event_id == wx.ID_CANCEL:
            
            if not self._CanCancel():
                
                return
                
            
        
        if not self.IsModal(): # in some rare cases (including spammy AutoHotkey, looks like), this can be fired before the dialog can clean itself up
            
            return
            
        
        self.EndModal( event_id )
        
    
class DialogThatResizes( NewDialog ):
    
    def __init__( self, parent, title, frame_key, style_override = None ):
        
        self._frame_key = frame_key
        
        NewDialog.__init__( self, parent, title, style_override = style_override )
        
    
class DialogThatTakesScrollablePanel( DialogThatResizes ):
    
    def __init__( self, parent, title, frame_key = 'regular_dialog', style_override = None ):
        
        self._panel = None
        
        DialogThatResizes.__init__( self, parent, title, frame_key, style_override = style_override )
        
        self._InitialiseButtons()
        
        self.Bind( EVT_OK, self.EventOK )
        self.Bind( CC.EVT_SIZE_CHANGED, self.EventChildSizeChanged )
        
    
    def _CanCancel( self ):
        
        return self._panel.CanCancel()
        
    
    def _GetButtonBox( self ):
        
        raise NotImplementedError()
        
    
    def _InitialiseButtons( self ):
        
        raise NotImplementedError()
        
    
    def _TryEndModal( self, value ):
        
        try:
            
            self.EndModal( value )
            
        except Exception as e:
            
            HydrusData.ShowText( 'This dialog seems to have been unable to close for some reason. I am printing the stack to the log. The dialog may have already closed, or may attempt to close now. Please inform hydrus dev of this situation. I recommend you restart the client if you can. If the UI is locked, you will have to kill it via task manager.' )
            
            HydrusData.PrintException( e )
            
            import traceback
            
            HydrusData.DebugPrint( ''.join( traceback.format_stack() ) )
            
            try:
                
                self.Close()
                
            except:
                
                HydrusData.ShowText( 'The dialog would not close on command.' )
                
            
            try:
                
                self.Destroy()
                
            except:
                
                HydrusData.ShowText( 'The dialog would not destroy on command.' )
                
            
        
    
    def DoOK( self ):
        
        raise NotImplementedError()
        
    
    def EventChildSizeChanged( self, event ):
        
        if self._panel is not None:
            
            # the min size here is to compensate for wx.Notebook and anything else that don't update virtualsize on page change
            
            ( current_panel_width, current_panel_height ) = self._panel.GetSize()
            ( desired_panel_width, desired_panel_height ) = self._panel.GetVirtualSize()
            ( min_panel_width, min_panel_height ) = self._panel.GetEffectiveMinSize()
            
            desired_delta_width = max( 0, desired_panel_width - current_panel_width, min_panel_width - current_panel_width )
            desired_delta_height = max( 0, desired_panel_height - current_panel_height, min_panel_height - current_panel_height )
            
            if desired_delta_width > 0 or desired_delta_height > 0:
                
                ExpandTLWIfPossible( self, self._frame_key, ( desired_delta_width, desired_delta_height ) )
                
            
        
    
    def EventOK( self, event ):
        
        if not self:
            
            return
            
        
        self.DoOK()
        
    
    def SetPanel( self, panel ):
        
        self._panel = panel
        
        buttonbox = self._GetButtonBox()
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( buttonbox, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        SetInitialTLWSizeAndPosition( self, self._frame_key )
        
        self._panel.SetupScrolling( scrollIntoView = False ) # this changes geteffectiveminsize calc, so it needs to be below settlwsizeandpos
        
        PostSizeChangedEvent( self ) # helps deal with some Linux/otherscrollbar weirdness where setupscrolling changes inherent virtual size
        
    
class DialogThatTakesScrollablePanelClose( DialogThatTakesScrollablePanel ):
    
    def _GetButtonBox( self ):
        
        buttonbox = wx.BoxSizer( wx.HORIZONTAL )
        
        buttonbox.Add( self._close, CC.FLAGS_VCENTER )
        
        return buttonbox
        
    
    def _InitialiseButtons( self ):
        
        self._close = wx.Button( self, id = wx.ID_OK, label = 'close' )
        self._close.Bind( wx.EVT_BUTTON, self.EventOK )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL )
        self._cancel.Hide()
        
    
class DialogNullipotent( DialogThatTakesScrollablePanelClose ):
    
    def __init__( self, parent, title ):
        
        DialogThatTakesScrollablePanelClose.__init__( self, parent, title )
        
    
    def DoOK( self ):
        
        if not self.IsModal():
            
            return
            
        
        SaveTLWSizeAndPosition( self, self._frame_key )
        
        self._TryEndModal( wx.ID_OK )
        
    
class DialogNullipotentVetoable( DialogThatTakesScrollablePanelClose ):
    
    def __init__( self, parent, title, style_override = None, hide_close_button = False ):
        
        DialogThatTakesScrollablePanelClose.__init__( self, parent, title, style_override = style_override )
        
        if hide_close_button:
            
            self._close.Hide()
            
            self.Bind( wx.EVT_CLOSE, self.EventOK ) # the close event no longer goes to the default button, since it is hidden, wew
            
        
    
    def DoOK( self ):
        
        if not self.IsModal():
            
            return
            
        
        try:
            
            self._panel.TryToClose()
            
        except HydrusExceptions.VetoException as e:
            
            message = HydrusData.ToUnicode( e )
            
            if len( message ) > 0:
                
                wx.MessageBox( message )
                
            
            return
            
        
        SaveTLWSizeAndPosition( self, self._frame_key )
        
        self._TryEndModal( wx.ID_OK )
        
    
class DialogThatTakesScrollablePanelApplyCancel( DialogThatTakesScrollablePanel ):
    
    def _GetButtonBox( self ):
        
        buttonbox = wx.BoxSizer( wx.HORIZONTAL )
        
        buttonbox.Add( self._apply, CC.FLAGS_VCENTER )
        buttonbox.Add( self._cancel, CC.FLAGS_VCENTER )
        
        return buttonbox
        
    
    def _InitialiseButtons( self ):
        
        self._apply = wx.Button( self, id = wx.ID_OK, label = 'apply' )
        self._apply.Bind( wx.EVT_BUTTON, self.EventOK )
        self._apply.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
    
class DialogEdit( DialogThatTakesScrollablePanelApplyCancel ):
    
    def __init__( self, parent, title, frame_key = 'regular_dialog' ):
        
        DialogThatTakesScrollablePanelApplyCancel.__init__( self, parent, title, frame_key = frame_key )
        
    
    def DoOK( self ):
        
        if not self.IsModal():
            
            return
            
        
        try:
            
            value = self._panel.GetValue()
            
        except HydrusExceptions.VetoException as e:
            
            message = HydrusData.ToUnicode( e )
            
            if len( message ) > 0:
                
                wx.MessageBox( message )
                
            
            return
            
        
        SaveTLWSizeAndPosition( self, self._frame_key )
        
        self._TryEndModal( wx.ID_OK )
        
    
class DialogManage( DialogThatTakesScrollablePanelApplyCancel ):
    
    def DoOK( self ):
        
        if not self.IsModal():
            
            return
            
        
        try:
            
            self._panel.CommitChanges()
            
        except HydrusExceptions.VetoException as e:
            
            message = HydrusData.ToUnicode( e )
            
            if len( message ) > 0:
                
                wx.MessageBox( message )
                
            
            return
            
        
        SaveTLWSizeAndPosition( self, self._frame_key )
        
        self._TryEndModal( wx.ID_OK )
        
    
class Frame( wx.Frame ):
    
    def __init__( self, parent, title, float_on_parent = True ):
        
        style = wx.DEFAULT_FRAME_STYLE
        
        if float_on_parent:
            
            style |= wx.FRAME_FLOAT_ON_PARENT
            
        
        wx.Frame.__init__( self, parent, title = title, style = style )
        
        self._new_options = HG.client_controller.new_options
        
        self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_FRAMEBK ) )
        
        self.SetIcon( HG.client_controller.frame_icon )
        
        self.Bind( wx.EVT_MENU_CLOSE, self.EventMenuClose )
        self.Bind( wx.EVT_MENU_HIGHLIGHT_ALL, self.EventMenuHighlight )
        self.Bind( wx.EVT_MENU_OPEN, self.EventMenuOpen )
        
        self._menu_stack = []
        self._menu_text_stack = []
        
        HG.client_controller.ResetIdleTimer()
        
    
    def EventMenuClose( self, event ):
        
        menu = event.GetMenu()
        
        if menu is not None and menu in self._menu_stack:
            
            index = self._menu_stack.index( menu )
            
            del self._menu_stack[ index ]
            
            previous_text = self._menu_text_stack.pop()
            
            status_bar = HG.client_controller.GetGUI().GetStatusBar()
            
            status_bar.SetStatusText( previous_text )
            
        
    
    def EventMenuHighlight( self, event ):
        
        if len( self._menu_stack ) > 0:
            
            text = ''
            
            menu = self._menu_stack[-1]
            
            while ClientGUIMenus.MenuIsDead( menu ):
                
                del self._menu_stack[-1]
                
                if len( self._menu_stack ) == 0:
                    
                    return
                    
                
                menu = self._menu_stack[-1]
                
            
            menu_item = menu.FindItemById( event.GetMenuId() )
            
            if menu_item is not None:
                
                text = menu_item.GetHelp()
                
            
            status_bar = HG.client_controller.GetGUI().GetStatusBar()
            
            status_bar.SetStatusText( text )
            
        
    
    def EventMenuOpen( self, event ):
        
        menu = event.GetMenu()
        
        if menu is not None:
            
            status_bar = HG.client_controller.GetGUI().GetStatusBar()
            
            previous_text = status_bar.GetStatusText()
            
            self._menu_stack.append( menu )
            
            self._menu_text_stack.append( previous_text )
            
        
    
class FrameThatResizes( Frame ):
    
    def __init__( self, parent, title, frame_key, float_on_parent = True ):
        
        self._frame_key = frame_key
        
        Frame.__init__( self, parent, title, float_on_parent )
        
        self.Bind( wx.EVT_SIZE, self.EventSizeAndPositionChanged )
        self.Bind( wx.EVT_MOVE_END, self.EventSizeAndPositionChanged )
        self.Bind( wx.EVT_CLOSE, self.EventSizeAndPositionChanged )
        self.Bind( wx.EVT_MAXIMIZE, self.EventSizeAndPositionChanged )
        
    
    def EventSizeAndPositionChanged( self, event ):
        
        SaveTLWSizeAndPosition( self, self._frame_key )
        
        event.Skip()
        
    
class FrameThatTakesScrollablePanel( FrameThatResizes ):
    
    def __init__( self, parent, title, frame_key = 'regular_dialog', float_on_parent = True ):
        
        self._panel = None
        
        FrameThatResizes.__init__( self, parent, title, frame_key, float_on_parent )
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'close' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventClose )
        
        self.Bind( EVT_OK, self.EventClose )
        self.Bind( CC.EVT_SIZE_CHANGED, self.EventChildSizeChanged )
        
        self.Bind( wx.EVT_CHAR_HOOK, self.EventCharHook )
        
    
    def EventCharHook( self, event ):
        
        ( modifier, key ) = ClientGUIShortcuts.ConvertKeyEventToSimpleTuple( event )
        
        if key == wx.WXK_ESCAPE:
            
            self.Close()
            
        else:
            
            event.Skip()
            
        
    
    def EventClose( self, event ):
        
        self.Close()
        
    
    def EventChildSizeChanged( self, event ):
        
        if self._panel is not None:
            
            # the min size here is to compensate for wx.Notebook and anything else that don't update virtualsize on page change
            
            ( current_panel_width, current_panel_height ) = self._panel.GetSize()
            ( desired_panel_width, desired_panel_height ) = self._panel.GetVirtualSize()
            ( min_panel_width, min_panel_height ) = self._panel.GetEffectiveMinSize()
            
            desired_delta_width = max( 0, desired_panel_width - current_panel_width, min_panel_width - current_panel_width )
            desired_delta_height = max( 0, desired_panel_height - current_panel_height, min_panel_height - current_panel_height )
            
            if desired_delta_width > 0 or desired_delta_height > 0:
                
                ExpandTLWIfPossible( self, self._frame_key, ( desired_delta_width, desired_delta_height ) )
                
            
        
    
    def SetPanel( self, panel ):
        
        self._panel = panel
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( self._ok, CC.FLAGS_LONE_BUTTON )
        
        self.SetSizer( vbox )
        
        SetInitialTLWSizeAndPosition( self, self._frame_key )
        
        self.Show( True )
        
        self._panel.SetupScrolling( scrollIntoView = False ) # this changes geteffectiveminsize calc, so it needs to be below settlwsizeandpos
        
        PostSizeChangedEvent( self ) # helps deal with some Linux/otherscrollbar weirdness where setupscrolling changes inherent virtual size
        
    
