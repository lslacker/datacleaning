import pywinauto


pwa_app = pywinauto.application.Application()

w_handle = pywinauto.findwindows.find_windows(title=u'Print to file', class_name='bosa_sdm_Microsoft Office Word 12.0')[0]
window = pwa_app.window_(handle=w_handle)
window.Click()