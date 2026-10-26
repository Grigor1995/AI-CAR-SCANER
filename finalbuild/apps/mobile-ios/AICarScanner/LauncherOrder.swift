import Foundation

/// Presentation order only. Workflow IDs remain stable regardless of tile position.
enum LauncherOrder {
    static func normalized(_ saved:String, defaults:[Int]) -> [Int] {
        var order:[Int]=[]
        for part in saved.split(separator:",") {
            if let id=Int(part), defaults.contains(id), !order.contains(id) {order.append(id)}
        }
        return order + defaults.filter {!order.contains($0)}
    }

    static func moving(_ order:[Int], source:Int, target:Int) -> [Int] {
        guard source != target, let from=order.firstIndex(of:source), let to=order.firstIndex(of:target) else {return order}
        var result=order
        result.remove(at:from);result.insert(source,at:to)
        return result
    }
}
