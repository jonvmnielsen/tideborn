#include "TidebornGatherNode.h"
#include "TidebornInventoryComponent.h"
#include "TidebornNameTagComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Engine.h"

ATidebornGatherNode::ATidebornGatherNode()
{
	PrimaryActorTick.bCanEverTick = false;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	RootComponent = Mesh;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeMesh.Succeeded())
	{
		Mesh->SetStaticMesh(CubeMesh.Object);
	}
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));
	Mesh->SetGenerateOverlapEvents(true);

	GatherVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("GatherVolume"));
	GatherVolume->SetupAttachment(RootComponent);
	GatherVolume->SetBoxExtent(FVector(80.f, 80.f, 120.f));
	GatherVolume->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	GatherVolume->SetCollisionResponseToAllChannels(ECR_Block);
	GatherVolume->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	GatherVolume->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	GatherVolume->SetHiddenInGame(true);
}

void ATidebornGatherNode::BeginPlay()
{
	Super::BeginPlay();

	SetActorScale3D(FVector(0.9f, 0.9f, 2.4f));

	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial")))
	{
		if (UMaterialInstanceDynamic* Dyn = UMaterialInstanceDynamic::Create(Base, this))
		{
			const FLinearColor Color = (ItemId == FName(TEXT("Stone")))
				? FLinearColor(0.55f, 0.55f, 0.6f)
				: FLinearColor(1.f, 0.45f, 0.05f);
			Dyn->SetVectorParameterValue(TEXT("Color"), Color);
			Mesh->SetMaterial(0, Dyn);
		}
	}

	const bool bStone = (ItemId == FName(TEXT("Stone")));
	if (UTidebornNameTagComponent* Tag = NewObject<UTidebornNameTagComponent>(this, TEXT("NameTag")))
	{
		Tag->HeightOffset = 160.f;
		Tag->Title = bStone ? TEXT("Stone Node") : TEXT("Wood Node");
		Tag->Subtitle = TEXT("Press E to gather");
		Tag->TitleColor = bStone ? FColor(180, 180, 200) : FColor(255, 160, 40);
		AddInstanceComponent(Tag);
		Tag->RegisterComponent();
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
