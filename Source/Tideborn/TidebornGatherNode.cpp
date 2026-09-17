#include "TidebornGatherNode.h"
#include "TidebornInventoryComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Engine.h"

ATidebornGatherNode::ATidebornGatherNode()
{
	PrimaryActorTick.bCanEverTick = false;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	RootComponent = Mesh;
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));
	Mesh->SetGenerateOverlapEvents(true);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> WoodMesh(TEXT("/Game/Tideborn/Meshes/SM_WoodStump.SM_WoodStump"));
	if (WoodMesh.Succeeded())
	{
		Mesh->SetStaticMesh(WoodMesh.Object);
	}

	GatherVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("GatherVolume"));
	GatherVolume->SetupAttachment(RootComponent);
	GatherVolume->SetBoxExtent(FVector(90.f, 90.f, 100.f));
	GatherVolume->SetRelativeLocation(FVector(0.f, 0.f, 60.f));
	GatherVolume->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	GatherVolume->SetCollisionResponseToAllChannels(ECR_Block);
	GatherVolume->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	GatherVolume->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	GatherVolume->SetHiddenInGame(true);
}

void ATidebornGatherNode::BeginPlay()
{
	Super::BeginPlay();

	const bool bStone = (ItemId == FName(TEXT("Stone")));
	if (bStone)
	{
		if (UStaticMesh* Stone = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Tideborn/Meshes/SM_StoneCluster.SM_StoneCluster")))
		{
			Mesh->SetStaticMesh(Stone);
		}
		SetActorScale3D(FVector(1.f));
		GatherVolume->SetBoxExtent(FVector(110.f, 110.f, 70.f));
		GatherVolume->SetRelativeLocation(FVector(0.f, 0.f, 40.f));
	}
	else
	{
		SetActorScale3D(FVector(1.f));
		GatherVolume->SetBoxExtent(FVector(90.f, 90.f, 100.f));
		GatherVolume->SetRelativeLocation(FVector(0.f, 0.f, 60.f));
	}
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
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(91001, 8.f, FColor::Red, TEXT("Tideborn: NO inventory on character"));
		}
		return true;
	}

	if (!Inv->AddItem(ItemId, AmountPerGather))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(91001, 6.f, FColor::Red, TEXT("Tideborn: inventory full"));
		}
		return true;
	}

	--RemainingUses;
	const FString Msg = FString::Printf(TEXT("Gathered %s x%d (node left %d)"), *ItemId.ToString(), AmountPerGather, RemainingUses);
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(91001, 8.f, FColor::Green, Msg);
	}

	if (RemainingUses <= 0)
	{
		Destroy();
	}
	return true;
}
