import Image from 'next/image'
import { useTheme } from 'nextra-theme-docs'
import { useEffect, useState } from 'react'
import LogoFullDark from '../public/images/logo-full-dark.svg'
import LogoFull from '../public/images/logo-full.svg'

export default function Logo({
  width,
  height,
}: {
  width?: number
  height?: number
}) {
  const { resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])

  if (!mounted) return null

  return (
    <Image
      src={resolvedTheme === 'dark' ? LogoFullDark : LogoFull}
      alt="NPi AI"
      width={width}
      height={height}
    />
  )
}
