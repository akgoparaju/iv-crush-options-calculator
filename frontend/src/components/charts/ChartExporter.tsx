import React, { useState, useRef } from 'react'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import { Download, Share2, Link, FileText } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { ChartExportOptions, ChartExportData } from '@/types/charts'
import { formatChartCurrency } from '@/utils/chartTheme'

interface ChartExporterProps {
  chartRef: React.RefObject<HTMLDivElement>
  data: ChartExportData
  fileName?: string
}

export const ChartExporter: React.FC<ChartExporterProps> = ({
  chartRef,
  data,
  fileName = 'options_analysis'
}) => {
  const [isExporting, setIsExporting] = useState(false)
  const [exportOptions, setExportOptions] = useState<ChartExportOptions>({
    format: 'pdf',
    includeCharts: true,
    includeAnalysis: true,
    includeDisclaimers: true,
    shareableLink: false,
    quality: 8,
    orientation: 'landscape'
  })

  // Generate PDF export
  const exportToPDF = async () => {
    if (!chartRef.current) return
    
    setIsExporting(true)
    try {
      // Create PDF document
      const pdf = new jsPDF({
        orientation: exportOptions.orientation,
        unit: 'mm',
        format: 'a4'
      })

      // Add header
      pdf.setFontSize(20)
      pdf.text('Options Trading Analysis Report', 20, 20)
      
      pdf.setFontSize(12)
      pdf.text(`Symbol: ${data.metadata.symbol}`, 20, 30)
      pdf.text(`Current Price: ${formatChartCurrency(data.metadata.currentPrice)}`, 20, 37)
      pdf.text(`Strategy: ${data.metadata.strategy}`, 20, 44)
      pdf.text(`Analysis Date: ${data.metadata.analysisDate}`, 20, 51)

      // Capture chart as image
      if (exportOptions.includeCharts && chartRef.current) {
        const canvas = await html2canvas(chartRef.current, {
          scale: exportOptions.quality ? exportOptions.quality / 5 : 2,
          logging: false,
          backgroundColor: '#ffffff'
        })
        
        const imgData = canvas.toDataURL('image/png')
        
        // Add chart image to PDF
        const imgWidth = 250
        const imgHeight = (canvas.height * imgWidth) / canvas.width
        pdf.addImage(imgData, 'PNG', 20, 60, imgWidth, imgHeight)
        
        // Add new page for analysis if needed
        if (exportOptions.includeAnalysis) {
          pdf.addPage()
        }
      }

      // Add analysis data
      if (exportOptions.includeAnalysis) {
        pdf.setFontSize(14)
        pdf.text('Analysis Details', 20, 20)
        
        pdf.setFontSize(10)
        let yPosition = 30
        
        // Add P&L scenarios
        if (data.data.pnlScenarios) {
          pdf.text('P&L Scenarios:', 20, yPosition)
          yPosition += 7
          
          data.data.pnlScenarios.slice(0, 5).forEach((scenario: any) => {
            pdf.text(
              `Price Change: ${scenario.priceChange.toFixed(1)}% | P&L: ${formatChartCurrency(scenario.pnlValues[0])}`,
              30,
              yPosition
            )
            yPosition += 5
          })
        }
        
        // Add Greeks data
        if (data.data.greeksTimeSeries) {
          yPosition += 5
          pdf.text('Greeks Analysis:', 20, yPosition)
          yPosition += 7
          
          const currentGreeks = data.data.greeksTimeSeries[Math.floor(data.data.greeksTimeSeries.length / 2)]
          pdf.text(`Delta: ${currentGreeks.delta.toFixed(3)}`, 30, yPosition)
          yPosition += 5
          pdf.text(`Gamma: ${currentGreeks.gamma.toFixed(3)}`, 30, yPosition)
          yPosition += 5
          pdf.text(`Theta: ${currentGreeks.theta.toFixed(3)}/day`, 30, yPosition)
          yPosition += 5
          pdf.text(`Vega: ${currentGreeks.vega.toFixed(3)}`, 30, yPosition)
        }
      }

      // Add disclaimers
      if (exportOptions.includeDisclaimers) {
        pdf.setFontSize(8)
        pdf.setTextColor(128, 128, 128)
        const pageHeight = pdf.internal.pageSize.height
        pdf.text(
          'This report is for educational purposes only. Not financial advice.',
          20,
          pageHeight - 20
        )
        pdf.text(
          'Past performance does not guarantee future results. Options trading involves risk.',
          20,
          pageHeight - 15
        )
      }

      // Save PDF
      pdf.save(`${fileName}_${new Date().toISOString().split('T')[0]}.pdf`)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  // Export to PNG
  const exportToPNG = async () => {
    if (!chartRef.current) return
    
    setIsExporting(true)
    try {
      const canvas = await html2canvas(chartRef.current, {
        scale: exportOptions.quality ? exportOptions.quality / 5 : 2,
        logging: false,
        backgroundColor: '#ffffff'
      })
      
      // Convert to blob and download
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `${fileName}_${new Date().toISOString().split('T')[0]}.png`
          a.click()
          URL.revokeObjectURL(url)
        }
      })
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  // Export to SVG
  const exportToSVG = () => {
    // SVG export would require converting the chart to SVG format
    // This is a simplified version
    const svgContent = `
      <svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
        <text x="50" y="50" font-size="20">Options Trading Analysis</text>
        <text x="50" y="80">Symbol: ${data.metadata.symbol}</text>
        <text x="50" y="100">Current Price: ${formatChartCurrency(data.metadata.currentPrice)}</text>
        <text x="50" y="120">Strategy: ${data.metadata.strategy}</text>
        <!-- Chart content would be rendered here -->
      </svg>
    `
    
    const blob = new Blob([svgContent], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${fileName}_${new Date().toISOString().split('T')[0]}.svg`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Export to JSON
  const exportToJSON = () => {
    const jsonContent = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonContent], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${fileName}_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Generate shareable link
  const generateShareableLink = () => {
    // In a real implementation, this would upload the data to a server
    // and return a shareable URL
    const baseUrl = window.location.origin
    const encodedData = btoa(JSON.stringify(data).slice(0, 2000)) // Limit size
    const shareUrl = `${baseUrl}/shared/${encodedData.slice(0, 20)}` // Mock URL
    
    navigator.clipboard.writeText(shareUrl)
    alert('Shareable link copied to clipboard!')
  }

  // Handle export based on format
  const handleExport = () => {
    switch (exportOptions.format) {
      case 'pdf':
        exportToPDF()
        break
      case 'png':
        exportToPNG()
        break
      case 'svg':
        exportToSVG()
        break
      case 'json':
        exportToJSON()
        break
    }
  }

  return (
    <div className="flex flex-col space-y-4 p-4 bg-slate-50 rounded-lg">
      <h4 className="text-sm font-semibold text-slate-900">Export Options</h4>
      
      {/* Format Selection */}
      <div className="flex flex-wrap gap-2">
        {(['pdf', 'png', 'svg', 'json'] as const).map(format => (
          <Button
            key={format}
            variant={exportOptions.format === format ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setExportOptions(prev => ({ ...prev, format }))}
          >
            {format.toUpperCase()}
          </Button>
        ))}
      </div>

      {/* Export Options */}
      <div className="space-y-2">
        <label className="flex items-center space-x-2 text-sm">
          <input
            type="checkbox"
            checked={exportOptions.includeCharts}
            onChange={(e) => setExportOptions(prev => ({
              ...prev,
              includeCharts: e.target.checked
            }))}
            className="rounded"
          />
          <span>Include Charts</span>
        </label>
        
        <label className="flex items-center space-x-2 text-sm">
          <input
            type="checkbox"
            checked={exportOptions.includeAnalysis}
            onChange={(e) => setExportOptions(prev => ({
              ...prev,
              includeAnalysis: e.target.checked
            }))}
            className="rounded"
          />
          <span>Include Analysis Data</span>
        </label>
        
        <label className="flex items-center space-x-2 text-sm">
          <input
            type="checkbox"
            checked={exportOptions.includeDisclaimers}
            onChange={(e) => setExportOptions(prev => ({
              ...prev,
              includeDisclaimers: e.target.checked
            }))}
            className="rounded"
          />
          <span>Include Disclaimers</span>
        </label>
      </div>

      {/* Quality Slider for image exports */}
      {(exportOptions.format === 'pdf' || exportOptions.format === 'png') && (
        <div className="space-y-1">
          <label className="text-sm text-slate-700">
            Quality: {exportOptions.quality}
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={exportOptions.quality}
            onChange={(e) => setExportOptions(prev => ({
              ...prev,
              quality: parseInt(e.target.value)
            }))}
            className="w-full"
          />
        </div>
      )}

      {/* Export Actions */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant="primary"
          size="sm"
          onClick={handleExport}
          disabled={isExporting}
        >
          <Download className="h-4 w-4 mr-1" />
          {isExporting ? 'Exporting...' : 'Export'}
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={generateShareableLink}
        >
          <Link className="h-4 w-4 mr-1" />
          Share Link
        </Button>
      </div>
    </div>
  )
}

export default ChartExporter