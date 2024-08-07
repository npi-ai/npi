import { useAtom } from 'jotai'
import { atomWithStorage } from 'jotai/utils'
import { Tabs as NextraTabs } from 'nextra/components'

const selectedIndexAtom = atomWithStorage('nextra-tab-index', 0)

export function Tabs(props) {
  const [selectedIndex, setSelectedIndex] = useAtom(selectedIndexAtom)

  return (
    <NextraTabs
      {...props}
      selectedIndex={selectedIndex}
      onChange={(idx) => setSelectedIndex(idx)}
    />
  )
}

Tabs.Tab = NextraTabs.Tab
