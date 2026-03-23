'use client'

import { useEffect, useRef } from 'react'

interface Star {
  x: number
  y: number
  radius: number
  opacity: number
  speed: number
  phase: number
  isGold: boolean
}

export default function StarBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationId: number
    let stars: Star[] = []

    function resize() {
      if (!canvas) return
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
      initStars()
    }

    function initStars() {
      stars = []
      const count = Math.min(200, Math.floor((canvas!.width * canvas!.height) / 5000))
      for (let i = 0; i < count; i++) {
        stars.push({
          x: Math.random() * canvas!.width,
          y: Math.random() * canvas!.height,
          radius: Math.random() * 1.5 + 0.5,
          opacity: Math.random() * 0.8 + 0.2,
          speed: Math.random() * 0.005 + 0.002,
          phase: Math.random() * Math.PI * 2,
          isGold: Math.random() < 0.15,
        })
      }
    }

    function draw(time: number) {
      if (!ctx || !canvas) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (const star of stars) {
        const twinkle = Math.sin(time * star.speed + star.phase) * 0.3 + 0.7
        const alpha = star.opacity * twinkle

        ctx.beginPath()
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2)

        if (star.isGold) {
          ctx.fillStyle = `rgba(201, 169, 110, ${alpha})`
          ctx.shadowColor = 'rgba(201, 169, 110, 0.4)'
          ctx.shadowBlur = 6
        } else {
          ctx.fillStyle = `rgba(240, 237, 232, ${alpha})`
          ctx.shadowColor = 'transparent'
          ctx.shadowBlur = 0
        }

        ctx.fill()
      }

      ctx.shadowBlur = 0
      animationId = requestAnimationFrame(draw)
    }

    resize()
    animationId = requestAnimationFrame(draw)
    window.addEventListener('resize', resize)

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-0 pointer-events-none"
      style={{ background: '#0A0A0F' }}
    />
  )
}
