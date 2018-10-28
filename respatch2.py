#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import division 
import wx
import configparser
import os,sys
import logging
import os.path
import re
import time
import locale
import subprocess


MODULE    = 'GameClientResource'
currdir = os.path.dirname(os.path.realpath(__file__))
rsync_exe = os.path.join(currdir,r'bin\rsync.exe')
cgypath_exe = os.path.join(currdir,r'bin\cygpath.exe')


def rsync_resource(RSYNCFILE,RSYNCIP,RSYNCDIR):
    RSYNC_CMD = ''.join([rsync_exe,' -rptDvzP --progress '])
    RSYNC_MASTER="%s::%s" %(RSYNCIP,MODULE)
    cgypathcmd = '%s "%s" -a' % (cgypath_exe,RSYNCFILE)
    (output,err) = pyShell(cgypathcmd)
    if not err:
        CGYFILE = output.decode('utf-8')
    else:
        f1.printlog(u'转换上传文件路径失败,cmd:%s' % cgypathcmd)
        return False
    rsyncmd = '%s "%s" %s/%s/' % (RSYNC_CMD,CGYFILE.strip(),RSYNC_MASTER,RSYNCDIR)
    (output,err) = pyShell(rsyncmd)
    if not err:
        f1.printlog('result: %s output: %s \n' % ('success',output))
        return True
    else:
        f1.printlog('running cmd: %s faild!!! Errorinfo: %s output: %s \n' % (rsyncmd,str(err),output))
        f1.printlog('同步数据失败...请排查后重试...\n')
        return False

def pyShell(cmd):
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    output,err=p.communicate()
    return (output,err)

def setup_logging(logfile = 'respatch'):
    fmt = '%(asctime)s  %(levelname)s %(message)s'
    logging.basicConfig(level=logging.DEBUG,
        format=fmt,
        datefmt='%a, %d %b %Y %H:%M:%S',
        filename=r'./logs/%s.log' % logfile,
        filemode='a')


class FileDropTarget(wx.FileDropTarget):
    def __init__(self, windows):  
          wx.FileDropTarget.__init__(self)
          self.windows = windows
  
    def OnDropFiles(self,  x,  y, filenames):
        filenamesstr = ""
        for file in filenames:
            filenamesstr += file
            filenamesstr += '\n'
        self.windows.SetValue(filenamesstr)
        return True


class puFrame1 ( wx.Frame ):    
    def __init__( self, parent=None ):
        wx.Frame.__init__ ( self, parent=None, id=-1, title = u'资源更新工具', size = ( 1200,610 ) )
        panel = wx.Panel(self, -1)
        self.Centre( wx.BOTH )
        self.statictext = wx.StaticText(panel,-1,u'项目名称',pos=(10,5))
        self.statictext = wx.StaticText(panel,-1,u'文件拖拽区',pos=(225,5))
        self.statictext = wx.StaticText(panel,-1,u'日志输出区',pos=(525,5))
        self.m_listproChoices = _sections_new
        self.m_listpro = wx.ListBox( panel, wx.ID_ANY, wx.Point( 10,30 ), wx.Size( 200,500 ), self.m_listproChoices)
        self.m_textCtrl1 = wx.TextCtrl(panel,wx.ID_ANY, wx.EmptyString, wx.Point(220,30), wx.Size(300,500), wx.HSCROLL|wx.TE_MULTILINE|wx.TE_READONLY)
        dropTarget = FileDropTarget(self.m_textCtrl1)
        self.m_textCtrl1.SetDropTarget(dropTarget)

        self.m_output = wx.TextCtrl(panel,wx.ID_ANY, wx.EmptyString, wx.Point(525,30), wx.Size(600,500), wx.TE_MULTILINE|wx.TE_READONLY)
        self.m_output.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BACKGROUND ) )
        self.m_output.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_APPWORKSPACE ) )
        self.m_button = wx.Button( panel, wx.ID_ANY, u'开始更新', wx.Point(560,534), wx.Size(100,30))
        self.m_button.Bind( wx.EVT_BUTTON, self.uploadsource )

    def __del__( self ):
        pass

    def printlog(self, message, type="info"):
        if type == 'warning':
            logging.warning(message)
        else:
            logging.info(message)
        self.m_output.AppendText(message)


    def getinspoint(self):
    	return self.m_output.GetInsertionPoint()

    def progressbarlog(self,point,message):
    	self.m_output.Replace(point,point + 100,message)

    def _uploadsource( self, event ):
        resource_file = self.m_textCtrl1.GetValue()
        if not resource_file:
            self.printlog(u'注意！！！请选择有效的文件\n', type='warning')
            return
        if self.m_listpro.GetSelection() == -1:
            self.printlog(u'注意！！！请选择要更新的项目\n', type='warning')
            return
        resource_file_list = resource_file.split('\n')
        del resource_file_list[-1]
        pro = self.m_listproChoices[self.m_listpro.GetSelection()]
        resource_filename = os.path.basename(resource_file)
        resource_path = os.path.dirname(resource_file)
        _rsyncdir=cf.get(pro,'rsyncdir')
        _rsyncservers=cf.get(pro,'rsyncip')
        self.printlog(u'>>>>>>>>>>>>>任务开始<<<<<<<<<<<<<<<\n', type='info')            
        self.printlog('本次更新项目为： %s.\n 本次上传目标源机为： %s. \n\n' % (pro, _rsyncservers))
        for _rsyncserver in _rsyncservers.split(','):
            self.printlog(u'开始上传目标源机： %s. \n' % _rsyncserver)
            for src in resource_file_list:
                self.printlog(u'开始上传： %s. \n' % src)
                ret = rsync_resource(src, _rsyncserver, _rsyncdir)
                if not ret:
                    self.printlog(u'上传失败！！！！请查看详细日志...\n\n', type='warning')
                    sys.exit(1)
            self.printlog(u'源机 %s 更新完成...\n\n' % _rsyncserver)
        self.printlog(u'>>>>>>>>>>>>>任务结束<<<<<<<<<<<<<<<\n',type='info')


    def uploadsource(self, event):
        import _thread
        _thread.start_new_thread(self._uploadsource,(event,))

def remove_BOM(config_path):
    content = open(config_path).read()
    content = re.sub(r"\xfe\xff","", content)
    content = re.sub(r"\xff\xfe","", content)
    content = re.sub(r"\xef\xbb\xbf","", content)
    open(config_path, 'w').write(content)

if __name__=='__main__':
    format_datetime = "%Y%m%d%H%M%S"
    logfile = time.strftime(format_datetime, time.localtime(time.time()))
    setup_logging(logfile)
    remove_BOM('./config.ini')
    cf = configparser.ConfigParser()
    cf.read('./config.ini',encoding='utf-8')
    _sections=cf.sections()
    _sections_new = []
    for _section in _sections:
        if _section != "global":
            _sections_new.append(_section)
    #ftp=MyFTP()
    app=wx.App()
    f1=puFrame1()
    f1.Show()
    app.MainLoop()
