
import customtkinter as ctk

import modules.ui.components.image_preview as img
import modules.ui.components.info as info
import modules.ui.components.selection as selc
import modules.ui.components.settings as set
import modules.ui.components.mouth_mask as mmask
import modules.ui.component as c
class Init:
    
    def Set(self, root: ctk.CTk) -> ctk.CTk:
        c.root=root
        c==img.image_component(c)
        c==info.info_component(c)
        c==selc.selection_component(c)
        c==set.right_collum_component(c)
        c==set.left_collum_component(c)
        c==set.middle_collum_component(c)
        c==mmask.mouth_mask_component(c)
        return c.root