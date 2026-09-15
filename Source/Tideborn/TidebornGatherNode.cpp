#include "TidebornGatherNode.h"
#include "TidebornInventoryComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ATidebornGatherNode::ATidebornGatherNode()
{
	PrimaryActorTick.bCanEverTick = false;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	RootComponent = Mesh;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeMesh.Succeeded())
	{
		Mesh->SetStaticMesh(CubeMesh.Object);
		Mesh->SetWorldScale3D(FVector(0.6f, 0.6f, 0.9f));
	}
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));
}

bool ATidebornGatherNode::Tideborn_TryInteract(AActor* Interactor)
{
	if (!Interactor || RemainingUses <= 0 || ItemId.IsNone())
	{
		return false;
	}

	UTidebornInventoryComponent* Inv = Interactor->FindComponentByClass<UTidebornInventoryComponent>();
	if (!Inv)
	{
		return false;
	}

	if (!Inv->AddItem(ItemId, AmountPerGather))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 2.f, FColor::Red, TEXT("Tideborn: inventory full"));
		}
		return true;
	}

	--RemainingUses;
	const FString Msg = FString::Printf(TEXT("Tideborn Gathered %s x%d (left %d)"), *ItemId.ToString(), AmountPerGather, RemainingUses);
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 2.5f, FColor::Green, Msg);
	}
	UE_LOG(LogTemp, Log, TEXT("%s"), *Msg);

	if (RemainingUses <= 0)
	{
		Destroy();
	}
	return true;
}
