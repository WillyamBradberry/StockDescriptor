Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName System.Windows.Forms

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batchPath = Join-Path $scriptDir "run_pipeline.bat"

$placeholder = "Select image folder..."

[xml]$xaml = @'
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    x:Name="Root"
    Title="Stock Descriptor"
    Width="560" Height="300"
    WindowStyle="None"
    AllowsTransparency="True"
    Background="Transparent"
    ResizeMode="NoResize"
    WindowStartupLocation="CenterScreen"
    FontFamily="Segoe UI">

    <Border CornerRadius="16" SnapsToDevicePixels="True">
        <Border.Background>
            <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
                <GradientStop Color="#1E2A44" Offset="0"/>
                <GradientStop Color="#0F1626" Offset="1"/>
            </LinearGradientBrush>
        </Border.Background>
        <Border.Effect>
            <DropShadowEffect BlurRadius="24" ShadowDepth="0" Color="#000000" Opacity="0.45"/>
        </Border.Effect>

        <Grid Margin="0">
            <Grid.RowDefinitions>
                <RowDefinition Height="46"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="Auto"/>
            </Grid.RowDefinitions>

            <!-- Title bar -->
            <Border x:Name="TitleBar" Grid.Row="0" CornerRadius="16,16,0,0" Background="#000000" Opacity="0.18" Cursor="Hand">
                <Grid>
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>
                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="18,0,0,0">
                        <Ellipse Width="12" Height="12" Fill="#4CAF50" Margin="0,0,10,0"/>
                        <TextBlock Text="Stock Descriptor - Pipeline" Foreground="#E8EEF7" FontSize="15" FontWeight="SemiBold" VerticalAlignment="Center"/>
                    </StackPanel>
                    <Button x:Name="CloseButton" Grid.Column="1" Width="34" Height="34" Margin="0,0,8,0"
                            Background="Transparent" BorderThickness="0" Cursor="Hand" ToolTip="Close">
                        <TextBlock Text="X" FontSize="14" Foreground="#E8EEF7"/>
                    </Button>
                </Grid>
            </Border>

            <!-- Content -->
            <Grid Grid.Row="1" Margin="24,18,24,8">
                <Grid.RowDefinitions>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="*"/>
                </Grid.RowDefinitions>

                <TextBlock Grid.Row="0" Text="Image folder" Foreground="#9FB2CC" FontSize="13" Margin="2,0,0,8"/>

                <Grid Grid.Row="1">
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>
                    <Border Grid.Column="0" CornerRadius="10" Background="#0C1322" BorderBrush="#2C3A57" BorderThickness="1" Margin="0,0,10,0">
                        <TextBox x:Name="FolderBox" Background="Transparent" BorderThickness="0"
                                 Foreground="#E8EEF7" FontSize="13" Padding="12,9,12,9" VerticalContentAlignment="Center"/>
                    </Border>
                    <Button x:Name="BrowseButton" Grid.Column="1" Width="110" Height="38" Cursor="Hand" BorderThickness="0">
                        <Button.Background>
                            <LinearGradientBrush StartPoint="0,0" EndPoint="0,1">
                                <GradientStop Color="#3A4A6B" Offset="0"/>
                                <GradientStop Color="#2A3854" Offset="1"/>
                            </LinearGradientBrush>
                        </Button.Background>
                        <TextBlock Text="Browse..." Foreground="#E8EEF7" FontSize="13" FontWeight="SemiBold"/>
                    </Button>
                </Grid>

                <TextBlock x:Name="StatusText" Grid.Row="2" Text="Choose a folder and press Run"
                           Foreground="#7E90AC" FontSize="12" Margin="2,14,0,0" TextWrapping="Wrap"/>
            </Grid>

            <!-- Run -->
            <Button x:Name="RunButton" Grid.Row="2" Height="46" Margin="24,0,24,22" Cursor="Hand" BorderThickness="0">
                <Button.Background>
                    <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
                        <GradientStop Color="#3DDC84" Offset="0"/>
                        <GradientStop Color="#1FA463" Offset="1"/>
                    </LinearGradientBrush>
                </Button.Background>
                <TextBlock Text="RUN PIPELINE" Foreground="#06210F" FontSize="14" FontWeight="Bold"/>
            </Button>
        </Grid>
    </Border>
</Window>
'@

$reader = (New-Object System.Xml.XmlNodeReader $xaml)
$window = [System.Windows.Markup.XamlReader]::Load($reader)

# Controls
$titleBar    = $window.FindName("TitleBar")
$closeBtn    = $window.FindName("CloseButton")
$folderBox   = $window.FindName("FolderBox")
$browseBtn   = $window.FindName("BrowseButton")
$runBtn      = $window.FindName("RunButton")
$statusText  = $window.FindName("StatusText")

# Watermark
$folderBox.Text = $placeholder
$folderBox.Foreground = [System.Windows.Media.Brushes]::Gray
$folderBox.Add_GotFocus({
    if ($folderBox.Text -eq $placeholder) {
        $folderBox.Text = ""
        $folderBox.Foreground = [System.Windows.Media.Brushes]::White
    }
})
$folderBox.Add_LostFocus({
    if ([string]::IsNullOrWhiteSpace($folderBox.Text)) {
        $folderBox.Text = $placeholder
        $folderBox.Foreground = [System.Windows.Media.Brushes]::Gray
    }
})

# Drag + close
$titleBar.Add_MouseLeftButtonDown({ param($s,$e) if ($e.ChangedButton -eq [System.Windows.Input.MouseButton]::Left) { $window.DragMove() } })
$closeBtn.Add_Click({ $window.Close() })

# Browse - modern Explorer-style dialog (not the old tree)
$browseBtn.Add_Click({
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.ValidateNames = $false
    $dialog.CheckFileExists = $false
    $dialog.CheckPathExists = $true
    $dialog.FileName = "Select a folder"
    $dialog.Title = "Select the image folder"
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $picked = Split-Path $dialog.FileName -Parent
        if ([string]::IsNullOrWhiteSpace($picked)) { $picked = $dialog.FileName }
        $folderBox.Text = $picked
        $folderBox.Foreground = [System.Windows.Media.Brushes]::White
    }
})

function Set-Status($msg, $color) {
    $action = [System.Action]{
        $statusText.Text = $msg
        $statusText.Foreground = [System.Windows.Media.BrushConverter]::new().ConvertFromString($color)
    }
    if ($window.Dispatcher.CheckAccess()) {
        $action.Invoke()
    } else {
        $window.Dispatcher.Invoke($action)
    }
}

# Run - hidden process, no terminal window, output streamed to status
$runBtn.Add_Click({
    $folder = $folderBox.Text.Trim()
    if ($folder -eq $placeholder) { $folder = "" }

    if ([string]::IsNullOrWhiteSpace($folder)) {
        Set-Status "Please select a folder first." "#FF6B6B"
        return
    }
    if (-not (Test-Path $folder -PathType Container)) {
        Set-Status "Folder not found: $folder" "#FF6B6B"
        return
    }
    if (-not (Test-Path $batchPath -PathType Leaf)) {
        Set-Status "Batch not found: $batchPath" "#FF6B6B"
        return
    }

    # Lock UI during run
    $runBtn.IsEnabled = $false
    $browseBtn.IsEnabled = $false
    Set-Status "Running pipeline for:`n$folder" "#3DDC84"

    # Tell the batch to launch child windows hidden (powershell -WindowStyle Hidden, pythonw)
    $env:STOCK_GUI_HIDDEN = "1"

    # Redirect batch output to a temp log; poll the file from the UI thread
    # (avoids capturing the Process object in a closure, which is unreliable in PS)
    $logFile = Join-Path $env:TEMP ("stock_pipe_" + [System.Guid]::NewGuid().ToString("N") + ".log")
    "" | Set-Content -Path $logFile -Encoding UTF8

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "cmd.exe"
    $psi.Arguments = "/c call `"$batchPath`" `"$folder`" > `"$logFile`" 2>&1 < nul"
    $psi.WorkingDirectory = $scriptDir
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    try {
        [void](Start-Process -FilePath $psi.FileName -ArgumentList $psi.Arguments -WorkingDirectory $psi.WorkingDirectory -WindowStyle Hidden -PassThru)
    } catch {
        Set-Status "Launch failed: $($_.Exception.Message)" "#FF6B6B"
        $runBtn.IsEnabled = $true
        $browseBtn.IsEnabled = $true
        return
    }

    # Poll the log file on the UI thread via a DispatcherTimer (no process object in closure)
    $lastLen = 0
    $done = $false
    $poll = New-Object System.Windows.Threading.DispatcherTimer
    $poll.Interval = [TimeSpan]::FromMilliseconds(200)
    $poll.Add_Tick({
        param($s, $e)
        try {
            if (Test-Path $logFile) {
                $txt = [System.IO.File]::ReadAllText($logFile, [System.Text.Encoding]::UTF8)
                $trimmed = $txt.TrimEnd()
                if ($trimmed.Length -gt $lastLen) {
                    $lastLen = $trimmed.Length
                    $lines = $trimmed -split "`n"
                    $last = $lines[-1]
                    Set-Status ("Running...`n" + $last) "#3DDC84"
                }
            }
            # Detect completion: batch writes a sentinel line
            if (Test-Path $logFile) {
                $content = [System.IO.File]::ReadAllText($logFile, [System.Text.Encoding]::UTF8)
                if ($content -match "=== Pipeline completed\. ===") {
                    if (-not $done) {
                        $done = $true
                        if ($s -ne $null) { $s.Stop() }
                        Set-Status "Pipeline finished successfully." "#3DDC84"
                        $runBtn.IsEnabled = $true
                        $browseBtn.IsEnabled = $true
                    }
                }
            }
        } catch {
            if ($s -ne $null) { $s.Stop() }
            Set-Status ("Read error: " + $_.Exception.Message) "#FF6B6B"
            $runBtn.IsEnabled = $true
            $browseBtn.IsEnabled = $true
        }
    })
    $poll.Start()
})

[void]$window.ShowDialog()